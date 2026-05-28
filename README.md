# StreamTranslation

Real-time speech transcription and translation for live streaming (OBS). Convert live speech (French, Chinese, etc.) to English subtitles in real-time.

## Features

- Real-time transcription using OpenAI Whisper (French, Chinese, English, etc.)
- Multi-language translation via DeepL with Azure fallback
- OBS integration - reads/writes simple text file (no plugins needed)
- Transcript history with auto-cleanup
- Fully customizable - glossary, banned phrases, VAD threshold
- Graceful fallback - continues if DeepL quota exceeded
- Fast & lightweight - runs on Windows/Mac/Linux

## Prerequisites

- Python 3.10+
- Working microphone
- Internet connection
- Three API keys (OpenAI, DeepL, optionally Azure)

## Required API Keys

### OpenAI (Whisper Transcription)
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Cost: ~\.02 per 15 minutes of audio

### DeepL (Translation)
1. Go to https://www.deepl.com/pro/account
2. Sign up free (no credit card)
3. Copy API key
4. Cost: FREE = 500k chars/month (~100 hours streaming)

### Azure Translator (Optional Fallback)
1. Go to https://portal.azure.com/
2. Create "Translator" resource
3. Copy API key
4. Cost: ~\/month if needed

## Installation (Step-by-Step)

### Step 1: Clone Repository
\\\powershell
git clone https://github.com/karlittoSR/StreamTranslation.git
cd StreamTranslation
\\\

### Step 2: Create Virtual Environment
\\\powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
\\\

### Step 3: Install Dependencies
\\\powershell
pip install -r requirements.txt
\\\

### Step 4: Set Up API Keys
\\\powershell
Copy-Item .env.example .env
notepad .env
\\\

Then fill in your actual API keys:
\\\
OPENAI_API_KEY=sk-your-key-here
DEEPL_AUTH_KEY=your-key-here
AZURE_AUTH_KEY=your-key-here
\\\

### Step 5: Find Your Microphone Device
\\\powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
\\\

Note your microphone number (usually 1 or higher).

### Step 6: Configure for Your Language

Edit \live_subs.py\ Config class:

**For French:**
\\\python
input_device_index: int = 1  # Your device number
deepl_target_lang: str = "EN-US"
transcription_prompt: str = (
    "You are transcribing French speedrunner speech from a live stream. "
    "Remove filler words and swear words. If unclear, leave blank."
)
\\\

**For Chinese (Mandarin):**
\\\python
input_device_index: int = 1  # Your device number
deepl_target_lang: str = "EN-US"
transcription_prompt: str = (
    "You are transcribing Chinese gamer speech from a live stream. "
    "Context: speedrunning and gaming. Remove filler words."
)
\\\

Also find the \	ranscribe_audio()\ function and change:
\\\python
# For French:
language="fr",

# For Chinese:
language="zh",
\\\

### Step 7: Configure OBS

1. Add Source → Text (GDI+)
2. Name: "Subtitles"
3. Check "Read from file"
4. Browse and select \subs_en.txt\ from StreamTranslation folder
5. Set font size 24-48pt
6. Position at bottom of screen
7. Click OK

### Step 8: Test

\\\powershell
python live_subs.py
\\\

Speak into your microphone. After 2 seconds of silence, you should see transcription and translation in OBS!

Press \Ctrl+C\ to stop.

### Step 9: Customize (Optional)

Create \glossary.json\:
\\\json
{
  "elden": "Elden Ring",
  "boss": "BOSS"
}
\\\

Edit \Config.banned_phrases\ to add filler words:
\\\python
banned_phrases: list = ["hum", "ah", "umm", "like", "you know"]
\\\

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| \sample_rate\ | 16000 | Must be 16000 for Whisper |
| \input_device_index\ | 1 | Your microphone device |
| \ad_energy_threshold\ | 0.024 | Speech sensitivity (0.01-0.05) |
| \nd_utterance_silence_sec\ | 2 | Pause to trigger transcription |
| \clear_after_sec\ | 2 | Subtitle display duration |
| \deepl_target_lang\ | EN-US | Target language |

## Language Support

**Transcription:** French (fr), Chinese (zh), English (en), Spanish (es), German (de), Japanese (ja), and more

**Translation:** EN-US, EN-GB, DE, FR, ZH, ES, JA, PT, RU, NL, PL, and more

## Troubleshooting

### No audio detected
- Run: \python -c "import sounddevice as sd; print(sd.query_devices())"\
- Check Windows Sound settings
- Lower \ad_energy_threshold\ to 0.01

### "DEEPL_AUTH_KEY not set"
- Created \.env\ file (copied from \.env.example\)?
- Paste actual key (no extra spaces)?
- Restart terminal

### Transcription is wrong language
- Change \language="fr"\ to \language="zh"\ in \	ranscribe_audio()\
- Adjust \	ranscription_prompt\ for your context

### Subtitles not in OBS
- Text source: Check "Read from file"
- Verify path to \subs_en.txt\
- Restart OBS

### Import errors
- Activate venv: \.\venv\Scripts\Activate.ps1\
- Reinstall: \pip install -r requirements.txt --upgrade\

## Costs

| Service | Monthly | Notes |
|---------|---------|-------|
| OpenAI | ~\ | 4 hrs/day streaming |
| DeepL | \ | Free tier: 500k chars |
| Azure | \ | Only if needed |
| **Total** | **~\** | Very affordable! |

## File Structure

\\\
StreamTranslation/
├── live_subs.py          # Main script
├── requirements.txt      # Dependencies
├── .env.example          # API keys template
├── README.md             # This file
├── subs_en.txt           # (Auto) Current subtitle
├── history_*.txt         # (Auto) Transcript history
└── glossary.json         # (Auto) Term corrections
\\\

## License

MIT - Free to use and modify

## Credits

Built for international streamers. Powered by OpenAI Whisper, DeepL, and Azure Translator.

Happy streaming!
