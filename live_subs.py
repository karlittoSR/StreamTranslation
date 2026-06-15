import os
import re
import queue
import json
import logging
import sys
import threading
from dataclasses import dataclass
from collections import deque
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional
import tempfile
import wave
import uuid
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import numpy as np
import sounddevice as sd
import requests
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration for live subtitle system."""
    sample_rate: int = 16000          # Audio sample rate in Hz (16 kHz is optimal for Whisper)
    chunk_sec: float = 0.4            # Duration of each audio chunk processed per VAD cycle (seconds); also the silence-detection resolution
    openai_model: str = "gpt-4o-transcribe"  # OpenAI model used for speech-to-text transcription
    vad_energy_threshold: float = 0.026      # RMS energy level above which audio is considered speech
    input_device_index: int = 1       # Sounddevice input device index (use sd.query_devices() to list)
    end_utterance_silence_sec: float = 1.7     # Seconds of silence required to trigger end-of-utterance (effective ~1.6s at chunk_sec=0.4)
    min_chars: int = 2                # Minimum character count for a transcription to be displayed (2 keeps short reactions like "Non"/"GG")
    clear_after_sec: float = 3        # Base seconds a subtitle stays on screen before being cleared
    max_utterance_samples: int = 220000      # Max samples buffered before a mid-speech flush is forced (~13.75s)
    history_file: str = "history_fr.txt"     # File where French transcriptions are appended with timestamps
    glossary_file: str = "glossary.json"     # JSON file mapping wrong terms to correct spellings/names
    subs_en_file: str = "subs_en.txt"        # Output file read by OBS as a subtitle text source
    deepl_target_lang: str = "EN-US"         # DeepL target language code for translation
    deepl_url: str = "https://api-free.deepl.com/v2/translate"  # DeepL free-tier REST API endpoint

    browser_host: str = "127.0.0.1"          # Host the local subtitle HTTP server binds to (loopback only)
    browser_port: int = 8765                 # Port the local subtitle HTTP server listens on
    browser_html_file: str = "subtitles.html"  # HTML page served to the OBS Browser Source
    subtitle_max_width_px: int = 1100        # Max width of the subtitle box in pixels (wrapping kicks in beyond this)
    subtitle_color: str = "#c3f9f6"          # Subtitle text colour (matches the stream overlay's cyan accent)
    subtitle_bottom_margin_px: int = 90      # Gap between the subtitle box and the bottom of the screen
    subtitle_bg_opacity: float = 0.35        # Box background opacity: 0 = invisible, 1 = solid black (lower = lighter)
    
    transcription_prompt: str = (
        "Diffusion d'un speedrun d'Elden Ring en français. Transcrivez les paroles mot pour mot, sans mots de remplissage. "
        "Si un passage est inintelligible, laissez-le vide plutôt que de deviner. "
        "Vocabulaire probable : Caelid, Leyndell, Sellia, Morgott, Maliketh, Radahn, Malenia, "
        "Margit, Mohg, Rennala, Death's Poker, quitout, glitchless, weapon art R1, kukri, "
        "timeloss, skip, splits, PB, RNG, any%, RL1, R1, R2."
    )
    
    def validate(self) -> None:
        """Validate all numeric config values and warn about missing optional files."""
        # Ensure audio parameters are physically meaningful
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.chunk_sec <= 0:
            raise ValueError("chunk_sec must be positive")
        if self.vad_energy_threshold < 0:
            raise ValueError("vad_energy_threshold must be non-negative")
        if self.input_device_index < 0:
            raise ValueError("input_device_index must be non-negative")
        # Glossary is optional — warn but don't abort if missing
        if not os.path.exists(self.glossary_file):
            logger.warning(f"Glossary file not found: {self.glossary_file}")
        logger.info("Configuration validated")


class SubtitleManager:
    """Manages subtitle file operations and auto-clear timer.

    Subtitles are shown in FIFO order: if one is currently on screen the next
    one is queued and displayed only after the current display period expires.
    This prevents a short trailing sentence from stomping a long one.
    """

    def __init__(self, config: Config):
        self.config = config
        self.clear_timer: Optional[threading.Timer] = None  # Active timer that will clear or advance the queue
        self.clear_token: int = 0        # Monotonically increasing token; each subtitle owns one, stale timers are ignored
        self.lock = threading.Lock()     # Protects all mutable state against races between the main thread and timer callbacks
        # Each entry in the queue is a (text, extra_sec) tuple waiting to be displayed
        self._queue: deque = deque()
        self._displaying: bool = False   # True while a subtitle is currently on screen

    def clear_subs_file(self) -> None:
        """Clear the subtitle file."""
        try:
            with open(self.config.subs_en_file, "w", encoding="utf-8") as f:
                f.write("")
            logger.debug("Subtitles cleared")
        except OSError as e:
            logger.error(f"Error clearing subs file: {e}")

    def _display_now(self, text: str, extra_sec: float) -> None:
        """Write text to the OBS subtitle file and arm a display timer. Must be called with lock held."""
        # Overwrite the subtitle file with the new text so OBS picks it up immediately
        try:
            with open(self.config.subs_en_file, "w", encoding="utf-8") as f:
                f.write(text.strip())
            logger.debug(f"Subtitle written: {text[:50]}...")
        except OSError as e:
            logger.error(f"Error writing subs file: {e}")

        # Total display duration = base time + bonus seconds for longer utterances
        display_sec = self.config.clear_after_sec + extra_sec
        # Bump the token so any previously armed timer is treated as stale
        self.clear_token += 1
        token = self.clear_token
        # Cancel any leftover timer from a previous subtitle
        if self.clear_timer is not None:
            self.clear_timer.cancel()
        # Schedule _on_timer to fire after the display window expires
        self.clear_timer = threading.Timer(
            display_sec,
            self._on_timer,
            args=(token,),
        )
        self.clear_timer.daemon = True
        self.clear_timer.start()
        self._displaying = True

    def _on_timer(self, token: int) -> None:
        """Timer callback: advance the FIFO queue or clear the screen if nothing is queued."""
        with self.lock:
            # Ignore this callback if a newer subtitle has already claimed the token
            if token != self.clear_token:
                return  # stale timer, a newer subtitle already took over
            self.clear_timer = None
            if self._queue:
                # Pop the next waiting subtitle and display it immediately
                next_text, next_extra = self._queue.popleft()
                logger.debug(f"Dequeuing next subtitle: {next_text[:50]}...")
                self._display_now(next_text, next_extra)
                # _displaying stays True, new timer armed inside _display_now
            else:
                # Nothing queued — clear the screen while still holding the
                # lock so no incoming write_subtitle call can be wiped by this clear.
                self._displaying = False
                # Bump token so a racing write_subtitle sees _displaying=False safely
                self.clear_token += 1
                try:
                    with open(self.config.subs_en_file, "w", encoding="utf-8") as f:
                        f.write("")
                    logger.debug("Subtitles cleared (timer expired, queue empty)")
                except OSError as e:
                    logger.error(f"Error clearing subs file: {e}")

    def write_subtitle(self, text: str, extra_sec: float = 0.0) -> None:
        """Public entry point: display a subtitle now or enqueue it for later if screen is busy."""
        with self.lock:
            if self._displaying:
                # A subtitle is currently on screen — add this one to the FIFO queue
                self._queue.append((text, extra_sec))
                logger.debug(
                    f"Subtitle queued (queue length: {len(self._queue)}): {text[:50]}..."
                )
            else:
                # Screen is free — display immediately
                self._display_now(text, extra_sec)

    def shutdown(self) -> None:
        """Cancel any pending timer, drain the queue, and blank the subtitle file."""
        with self.lock:
            # Stop any running display timer
            if self.clear_timer is not None:
                self.clear_timer.cancel()
                self.clear_timer = None
            # Invalidate the token so stale timer callbacks are harmless
            self.clear_token += 1
            # Drop all queued subtitles — no point showing them after shutdown
            self._queue.clear()
            self._displaying = False
        # Blank the OBS text file so nothing lingers on screen
        self.clear_subs_file()


class TextProcessor:
    """Handles text sanitization and glossary corrections."""
    
    def __init__(self, config: Config, glossary: dict):
        self.config = config
        self.glossary = glossary
    
    def sanitize(self, text: str, apply_glossary: bool = True) -> str:
        """Optionally apply glossary corrections and normalise whitespace.

        apply_glossary should be False for already-translated English text: the
        glossary maps French mishearings (e.g. "force" -> "Forsa") and would
        corrupt legitimate English words.
        """
        if not text:
            return ""

        out = text

        # Replace misspelled terms with the correct form — French side only
        if apply_glossary:
            for wrong_term, correct_term in self.glossary.items():
                out = re.sub(
                    r"\b" + re.escape(wrong_term) + r"\b",
                    correct_term,
                    out,
                    flags=re.IGNORECASE
                )

        # Trim leading/trailing whitespace, collapse internal spaces, and remove leading punctuation
        out = out.strip()
        out = re.sub(r"\s+", " ", out)                       # collapse multiple spaces into one
        out = re.sub(r"^[\-\–\—\•\·\|]+", "", out).strip()  # strip leading dash/bullet artefacts
        
        return out


class HistoryManager:
    """Manages transcription history."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def append(self, text: str) -> None:
        """Append a transcribed line with a French-locale timestamp to the history file."""
        # Format the current local time in French date style
        ts = datetime.now().astimezone().strftime(" - le %d/%m/%Y à %H:%M")
        try:
            with open(self.config.history_file, "a", encoding="utf-8") as f:
                f.write(f"{text.strip()}{ts}\n")
        except OSError as e:
            logger.error(f"Error writing history: {e}")
    
    def cleanup(self, days_to_keep: int = 30) -> None:
        """Read the history file line by line and discard entries older than days_to_keep."""
        if not os.path.exists(self.config.history_file):
            return
        
        try:
            # Any line whose timestamp is before this date will be removed
            cutoff_date = datetime.now().astimezone() - timedelta(days=days_to_keep)
            kept_lines = []
            removed_count = 0
            
            # Loop over every line in the history file and decide whether to keep it
            with open(self.config.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line:
                        continue  # skip blank lines
                    
                    # Extract timestamp from line (format: " - le %d/%m/%Y à %H:%M")
                    if " - le " in line:
                        try:
                            # Split on ' - le ' to isolate the date/time portion
                            ts_str = line.split(" - le ")[1]
                            line_date = datetime.strptime(ts_str, "%d/%m/%Y à %H:%M")
                            # Attach the local timezone so comparison with cutoff_date is valid
                            line_date = line_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
                            
                            if line_date > cutoff_date:
                                kept_lines.append(line)  # recent enough — keep it
                            else:
                                removed_count += 1        # too old — discard
                        except (ValueError, IndexError):
                            # If the timestamp can't be parsed, keep the line to avoid data loss
                            kept_lines.append(line)
                    else:
                        # No timestamp found — keep unconditionally
                        kept_lines.append(line)
            
            # Rewrite the file with only the kept lines
            with open(self.config.history_file, "w", encoding="utf-8") as f:
                for line in kept_lines:
                    f.write(f"{line}\n")
            
            if removed_count > 0:
                logger.info(f"History cleanup: removed {removed_count} lines older than {days_to_keep} days")
        
        except Exception as e:
            logger.error(f"Error cleaning history: {e}")


class TranslationHandler:
    """Handles translation with DeepL primary and Azure fallback on quota exceeded."""
    
    def __init__(self, config: Config):
        self.config = config
        self.deepl_auth_key = os.environ.get("DEEPL_AUTH_KEY", "").strip()   # DeepL API key from environment
        self.azure_auth_key = os.environ.get("AZURE_AUTH_KEY", "").strip()   # Azure Translator key from environment
        self.azure_location = "westeurope"                                    # Azure region where the resource is deployed
        self.azure_endpoint = "https://api.cognitive.microsofttranslator.com" # Azure Translator REST base URL
        self.deepl_exhausted = False  # Flipped to True when DeepL returns HTTP 456 (monthly quota reached)
        # Reuse one HTTP connection across translations so we don't pay a fresh
        # TLS handshake (~100-300ms) on every line. Both DeepL and Azure benefit.
        self.session = requests.Session()

        # Warn at startup if keys are missing so the user knows translation is degraded
        if not self.deepl_auth_key:
            logger.warning("DEEPL_AUTH_KEY not set. Translation disabled.")
        if not self.azure_auth_key:
            logger.warning("AZURE_AUTH_KEY not set. Azure fallback will not work.")
    
    def _get_azure_target_lang(self) -> str:
        """Convert a DeepL language code (e.g. EN-US) to the Azure format (e.g. en)."""
        # DeepL uses regional codes like EN-US; Azure only needs the base language code
        lang_code = self.config.deepl_target_lang.split("-")[0].lower()
        return lang_code
    
    def _translate_deepl(self, text: str) -> Optional[str]:
        """Translate via DeepL. Returns None on quota exceeded, empty string on other errors."""
        if not text or not self.deepl_auth_key:
            return ""
        
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.deepl_auth_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "text": text,
            "target_lang": self.config.deepl_target_lang,
        }
        
        try:
            response = self.session.post(
                self.config.deepl_url,
                headers=headers,
                data=data,
                timeout=8
            )
            
            # Check for quota exceeded error (HTTP 456)
            if response.status_code == 456:
                logger.warning("DeepL quota exceeded (500k characters limit reached). Switching to Azure Translator.")
                self.deepl_exhausted = True
                return None
            
            response.raise_for_status()
            
            payload = response.json()
            translations = payload.get("translations", [])
            if not translations:
                logger.warning("No translations returned from DeepL")
                return ""
            
            result = translations[0].get("text", "").strip()
            logger.debug(f"DeepL translation: {result[:50]}...")
            return result
            
        except requests.exceptions.Timeout:
            logger.error("DeepL request timeout")
            return ""
        except requests.exceptions.HTTPError as e:
            logger.error(f"DeepL HTTP error {response.status_code}: {response.text[:200]}")
            return ""
        except (KeyError, ValueError) as e:
            logger.error(f"DeepL response parsing error: {e}")
            return ""
        except Exception as e:
            logger.error(f"DeepL error: {e}")
            return ""
    
    def _translate_azure(self, text: str) -> str:
        """Translate via Azure Translator. Returns empty string on failure."""
        if not text or not self.azure_auth_key:
            return ""
        
        path = '/translate'
        constructed_url = self.azure_endpoint + path
        
        params = {
            'api-version': '3.0',
            'from': 'fr',  # Source language
            'to': [self._get_azure_target_lang()]
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': self.azure_auth_key,
            'Ocp-Apim-Subscription-Region': self.azure_location,
            'Content-Type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        
        body = [{'text': text}]
        
        try:
            response = self.session.post(
                constructed_url,
                params=params,
                headers=headers,
                json=body,
                timeout=8
            )
            response.raise_for_status()
            
            payload = response.json()
            if not payload or not isinstance(payload, list):
                logger.warning("Invalid Azure response format")
                return ""
            
            translations = payload[0].get("translations", [])
            if not translations:
                logger.warning("No translations returned from Azure")
                return ""
            
            result = translations[0].get("text", "").strip()
            logger.debug(f"Azure translation: {result[:50]}...")
            return result
            
        except requests.exceptions.Timeout:
            logger.error("Azure request timeout")
            return ""
        except requests.exceptions.HTTPError as e:
            logger.error(f"Azure HTTP error {response.status_code}: {response.text[:200]}")
            return ""
        except (KeyError, ValueError) as e:
            logger.error(f"Azure response parsing error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Azure error: {e}")
            return ""
    
    def translate(self, text: str) -> str:
        """Translate text. Uses DeepL first, falls back to Azure on quota exceeded."""
        if not text:
            return ""
        
        # If DeepL quota already exhausted, use Azure directly
        if self.deepl_exhausted:
            return self._translate_azure(text)
        
        # Try DeepL first
        result = self._translate_deepl(text)
        
        # If quota exceeded try Azure
        if result is None:
            return self._translate_azure(text)
        
        return result



def load_glossary(glossary_file: str) -> dict:
    """Load the term-correction glossary from a JSON file. Returns empty dict on any error."""
    # Glossary is optional — return empty dict if the file doesn't exist yet
    if not os.path.exists(glossary_file):
        logger.warning(f"Glossary file not found: {glossary_file}")
        return {}
    
    try:
        with open(glossary_file, "r", encoding="utf-8") as f:
            return json.load(f)  # expected format: {"wrong_term": "correct_term", ...}
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error loading glossary: {e}")
        return {}


@contextmanager
def temporary_wav(sample_rate: int):
    """Context manager that creates a temp WAV file path, yields it, then deletes the file."""
    tmp_path = None
    try:
        # Create an empty named file so we have a unique path; the caller will write audio into it
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        yield tmp_path
    finally:
        # Always attempt cleanup even if an exception was raised inside the with block
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError as e:
                logger.warning(f"Could not delete temp file {tmp_path}: {e}")


def audio_to_wav(audio_data: np.ndarray, sample_rate: int, wav_path: str) -> None:
    """Encode a float32 numpy audio array as a mono 16-bit PCM WAV file."""
    # Clamp values to [-1, 1] to prevent integer overflow, then scale to 16-bit range
    pcm16 = np.clip(audio_data, -1.0, 1.0)
    pcm16 = (pcm16 * 32767).astype(np.int16)
    
    try:
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)           # mono audio
            wf.setsampwidth(2)           # 2 bytes per sample = 16-bit
            wf.setframerate(sample_rate) # must match the recording sample rate
            wf.writeframes(pcm16.tobytes())
    except OSError as e:
        logger.error(f"Error writing WAV file: {e}")
        raise


def transcribe_audio(client: OpenAI, wav_path: str, config: Config) -> str:
    """Send a WAV file to the OpenAI transcription API and return the raw French text."""
    try:
        with open(wav_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=config.openai_model,          # model configured in Config (e.g. gpt-4o-transcribe)
                file=audio_file,
                response_format="text",              # return plain text, not JSON
                prompt=config.transcription_prompt,  # system-level context to improve accuracy
                language="fr",                       # hint to the model that audio is French
            )
            # API may return None on empty audio; cast to str to be safe
            result = str(response).strip() if response else ""
            logger.debug(f"Transcription result: {result[:50]}...")
            return result
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""


def write_browser_html(config: Config) -> None:
    """Generate the HTML page that the OBS Browser Source polls for subtitles.

    The page fetches subs_en_file every 150 ms and shows a semi-transparent box
    only when the file is non-empty, so the background disappears with the text.
    """
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: transparent;
    overflow: hidden;
  }}

  body {{
    display: flex;
    align-items: flex-end;
    justify-content: center;
    font-family: 'Funnel Sans', Arial, Helvetica, sans-serif;
  }}

  #subtitle {{
    display: none;
    max-width: {config.subtitle_max_width_px}px;
    margin-bottom: {config.subtitle_bottom_margin_px}px;
    padding: 10px 18px;
    border-radius: 8px;

    background: rgba(0, 0, 0, {config.subtitle_bg_opacity});
    color: {config.subtitle_color};

    font-size: 28px;
    font-weight: 600;
    line-height: 1.25;
    text-align: center;

    white-space: normal;
    overflow-wrap: break-word;
    word-break: normal;

    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.85);
    box-sizing: border-box;
  }}
</style>
</head>
<body>
  <div id="subtitle"></div>

<script>
const subtitle = document.getElementById("subtitle");
let lastText = "";

async function updateSubtitle() {{
  try {{
    const response = await fetch("{config.subs_en_file}?t=" + Date.now(), {{
      cache: "no-store"
    }});

    const text = (await response.text()).trim();

    if (text !== lastText) {{
      lastText = text;
      subtitle.textContent = text;

      if (text.length > 0) {{
        subtitle.style.display = "block";
      }} else {{
        subtitle.style.display = "none";
      }}
    }}
  }} catch (e) {{
    subtitle.style.display = "none";
  }}
}}

setInterval(updateSubtitle, 150);
updateSubtitle();
</script>
</body>
</html>
"""
    try:
        with open(config.browser_html_file, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Browser subtitle page written: {config.browser_html_file}")
    except OSError as e:
        logger.error(f"Error writing browser HTML file: {e}")
        raise


class _QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that doesn't log every request.

    The OBS page polls subs_en.txt ~7x/second, so the default per-request
    logging would flood the console. We silence it and rely on the single
    startup line instead.
    """

    def log_message(self, format, *args):
        pass  # suppress per-request access logging


def start_subtitle_http_server(config: Config) -> ThreadingHTTPServer:
    """Start a loopback HTTP server that serves the HTML page and subs_en_file to OBS.

    Runs in a daemon thread so it shuts down with the process. Files are served
    from the current working directory (where subs_en.txt and the HTML live).
    """
    directory = os.getcwd()

    # Bind the quiet request handler to the working directory so it serves our files
    handler = partial(_QuietHTTPRequestHandler, directory=directory)

    server = ThreadingHTTPServer(
        (config.browser_host, config.browser_port),
        handler,
    )

    # Serve in the background so the main transcription loop is never blocked
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    logger.info(
        f"🌐 OBS Browser Source URL: "
        f"http://{config.browser_host}:{config.browser_port}/{config.browser_html_file}"
    )

    return server


def main():
    """Main transcription loop."""
    config = Config()

    # Stand up the local subtitle web page + server for the OBS Browser Source
    write_browser_html(config)
    subtitle_http_server = start_subtitle_http_server(config)
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Load glossary
    glossary = load_glossary(config.glossary_file)
    
    # Initialize components
    client = OpenAI()
    subtitle_manager = SubtitleManager(config)
    text_processor = TextProcessor(config, glossary)
    history_manager = HistoryManager(config)
    history_retention_days = 30
    history_manager.cleanup(days_to_keep=history_retention_days)
    translator = TranslationHandler(config)
    
    # Audio buffer using deque for efficiency
    audio_q: queue.Queue = queue.Queue()
    buffer = deque(maxlen=int(config.sample_rate * config.chunk_sec * 2))
    
    def audio_callback(indata, frames, time_info, status):
        """Sounddevice callback for audio input."""
        if status:
            logger.warning(f"Audio status: {status}")
        audio_q.put(indata.copy())
    
    # Number of audio samples consumed per main-loop iteration
    chunk_size = int(config.sample_rate * config.chunk_sec)

    def extra_display_sec(sample_count: int) -> float:
        """Return bonus display seconds proportional to how long the streamer spoke."""
        # Very long utterance (≥ 200 000 samples ≈ 12.5 s): give 6 extra seconds
        if sample_count >= 200000:
            return 6.0
        # Long utterance (≥ 100 000 samples ≈ 6.25 s): give 3 extra seconds
        elif sample_count >= 100000:
            return 3.0
        # Medium utterance (≥ 32 000 samples ≈ 2 s): give 2 extra second
        elif sample_count >= 32000:
            return 2.0
        # Short utterance: no bonus, use only the base clear_after_sec
        return 0.0

    def process_utterance(audio_samples: np.ndarray) -> None:
        """Full pipeline for one audio block: WAV encode → transcribe → sanitise → translate → display."""
        fr_text = ""
        # Write samples to a temporary WAV file for the API, then clean up automatically
        with temporary_wav(config.sample_rate) as wav_path:
            try:
                audio_to_wav(audio_samples, config.sample_rate, wav_path)
                fr_text = transcribe_audio(client, wav_path, config)
            except Exception as e:
                logger.error(f"Transcription failed: {e}")

        # Remove filler words and apply glossary corrections to the raw French text
        fr_text = text_processor.sanitize(fr_text)
        # Discard transcriptions that are too short to be meaningful
        if not fr_text or len(fr_text) < config.min_chars:
            logger.debug(f"Skipping short text: '{fr_text}'")
            return

        # Log and persist the French transcription
        logger.info(f"FR: {fr_text}")
        history_manager.append(fr_text)

        # Translate to English; fall back to French if translation fails
        en_text = translator.translate(fr_text)
        if not en_text:
            en_text = fr_text
            logger.info("Using French text as fallback")

        # Sanitise the translated text and push it to OBS with the appropriate display duration.
        # Skip the glossary here — it targets French mishearings and would mangle English.
        en_text = text_processor.sanitize(en_text, apply_glossary=False)
        extra = extra_display_sec(audio_samples.size)  # bonus seconds based on utterance length
        subtitle_manager.write_subtitle(en_text, extra_sec=extra)
        logger.info(f"EN: {en_text} [display +{extra:.0f}s extra]")

    # Hand finished utterances to a single background worker so the capture/VAD
    # loop never blocks on the transcription + translation network round-trips.
    # One worker (not a pool) keeps subtitles in the order they were spoken.
    work_q: queue.Queue = queue.Queue()

    def transcription_worker():
        """Consume audio blocks and run the full transcribe/translate/display pipeline."""
        while True:
            item = work_q.get()
            if item is None:  # sentinel: shut the worker down
                work_q.task_done()
                break
            try:
                process_utterance(item)
            except Exception as e:
                logger.error(f"Worker error processing utterance: {e}")
            finally:
                work_q.task_done()

    worker_thread = threading.Thread(target=transcription_worker, daemon=True)
    worker_thread.start()

    try:
        logger.info(f"🎤 Starting live subtitle transcription")
        logger.info(f"   Device: {config.input_device_index}, Sample rate: {config.sample_rate} Hz")
        logger.info(f"   Chunk: {config.chunk_sec}s, VAD threshold: {config.vad_energy_threshold}")
        max_extra = extra_display_sec(config.max_utterance_samples)
        logger.info(f"   Auto-clear subtitles after {config.clear_after_sec}s (short) to {config.clear_after_sec + max_extra}s (very long utterance)")
        
        if translator.deepl_auth_key:
            logger.info(f"🌍 DeepL translation enabled -> {config.deepl_target_lang}")
        else:
            logger.warning("🌍 DeepL translation disabled (DEEPL_AUTH_KEY not set)")
        
        with sd.InputStream(
            device=config.input_device_index,
            channels=1,
            samplerate=config.sample_rate,
            callback=audio_callback,
            dtype="float32",
            blocksize=0,
        ):
            utterance_audio = np.zeros((0,), dtype=np.float32)
            silence_sec = 0.0
            
            # Main processing loop — runs forever until interrupted
            while True:
                # Inner loop: keep pulling audio chunks from the callback queue until
                # we have accumulated enough samples to fill one full chunk_size window
                while len(buffer) < chunk_size:
                    try:
                        new_audio = audio_q.get(timeout=1.0)  # block up to 1 s waiting for audio
                        buffer.extend(new_audio.flatten())     # append flat samples to the deque
                    except queue.Empty:
                        continue  # no audio arrived yet — loop back and wait again
                
                # Slice exactly chunk_size samples out of the front of the buffer
                chunk = np.array(list(buffer)[:chunk_size], dtype=np.float32)
                # Remove the consumed samples from the deque one by one
                for _ in range(chunk_size):
                    buffer.popleft() if buffer else None
                
                # Compute RMS energy of the chunk to decide speech vs silence (VAD)
                energy = float(np.sqrt(np.mean(chunk ** 2)))
                
                if energy > config.vad_energy_threshold:
                    # Speech detected — append chunk to the current utterance buffer
                    utterance_audio = np.concatenate([utterance_audio, chunk])
                    silence_sec = 0.0
                    logger.info(f"Speech detected (energy: {energy:.4f})")

                    # Mid-speech flush loop: if the utterance grows beyond the max sample cap,
                    # slice off a full block and send it to the API without waiting for silence
                    while utterance_audio.size >= config.max_utterance_samples:
                        block = utterance_audio[:config.max_utterance_samples].copy()
                        utterance_audio = utterance_audio[config.max_utterance_samples:]  # keep the remainder
                        logger.info(f"Max utterance size reached, flushing {block.size} samples")
                        work_q.put(block)
                else:
                    # Silence detected — accumulate silence duration
                    silence_sec += config.chunk_sec
                    logger.debug(f"Silence ({silence_sec:.2f}s, energy: {energy:.4f})")
                
                # End-of-utterance detection: enough silence has elapsed and we have buffered audio
                if silence_sec >= config.end_utterance_silence_sec and utterance_audio.size > 0:
                    logger.info(f"End of utterance detected ({utterance_audio.size} samples)")
                    to_transcribe = utterance_audio.copy()          # copy for processing
                    utterance_audio = np.zeros((0,), dtype=np.float32)  # reset the buffer
                    silence_sec = 0.0
                    work_q.put(to_transcribe)
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        subtitle_manager.shutdown()
        sys.exit(0)
    except sd.PortAudioError as e:
        logger.error(f"Audio device error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        # Signal the worker to stop and give it a moment to finish the current item
        work_q.put(None)
        worker_thread.join(timeout=10)
        subtitle_manager.shutdown()
        history_manager.cleanup(days_to_keep=history_retention_days)
        # Stop the local Browser Source HTTP server if it was started
        try:
            subtitle_http_server.shutdown()
        except Exception:
            pass
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
