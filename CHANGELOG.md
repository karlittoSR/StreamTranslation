# Changelog

All notable changes to StreamTranslation are documented here.

## [1.0.0] - 2024-01-15

### Initial Release

**Features:**
- Real-time speech transcription via OpenAI Whisper
- Multi-language support (French, Chinese, English, etc.)
- DeepL translation with Azure Translator fallback
- OBS text file integration (no plugins needed)
- Voice Activity Detection (VAD) for automatic speech detection
- Transcript history with auto-cleanup
- Customizable glossary for term corrections
- Configurable banned phrases (filler words removal)
- Graceful API fallback on quota exceeded
- Thread-safe subtitle queue management
- Comprehensive error handling and logging

**Installation:**
- Python 3.10+ support
- Virtual environment setup script
- Comprehensive README with step-by-step guide
- Quick start guide for rapid setup

**Configuration:**
- Dataclass-based configuration system
- Customizable microphone device selection
- VAD energy threshold adjustment
- Display duration per subtitle
- Subtitle file output path
- History file management

**Documentation:**
- README.md with full installation guide
- QUICKSTART.md for rapid 5-minute setup
- Code comments explaining key components
- Example files (.env.example, config_example.yaml, glossary_example.json)

**API Support:**
- OpenAI Whisper (transcription)
- DeepL API (primary translation)
- Azure Translator (fallback)

**Tested On:**
- Windows 10/11
- Python 3.10, 3.11, 3.12

---

## [1.1.0] - 2026-06-15

### OBS Browser Source & Pipeline Rework

**Added:**
- OBS Browser Source integration: a local loopback HTTP server (`127.0.0.1:8765`) serves a generated `subtitles.html` page that OBS polls for live subtitles — no more text-source file reload quirks
- Auto-generated, styled subtitle overlay (configurable max width, text colour, bottom margin, and background opacity; Funnel Sans font with fade in/out)
- Dedicated background transcription worker: capture/VAD no longer blocks on transcribe/translate, and a single worker preserves spoken order
- `start_subtitles.bat` launcher for one-click startup
- New config options: `browser_host`, `browser_port`, `browser_html_file`, `subtitle_max_width_px`, `subtitle_color`, `subtitle_bottom_margin_px`, `subtitle_bg_opacity`

**Changed:**
- VAD/display tuning: `chunk_sec` lowered to 0.4 (finer silence-detection resolution), `vad_energy_threshold` raised to 0.026, `min_chars` lowered to 2 (keeps short reactions like "Non"/"GG")
- Translation now reuses a single `requests.Session` (HTTP connection reuse) instead of opening a fresh connection per request
- `sanitize()` gained an `apply_glossary` flag for finer control over term correction
- Quiet HTTP request logging so the ~7 req/s OBS polling doesn't flood the log

**Fixed:**
- Graceful shutdown: worker is drained via a sentinel and the HTTP server is shut down cleanly on exit

**Housekeeping:**
- Personal `glossary.json` is now gitignored (use `glossary_example.json` as the template)

---

## Known Issues

- VAD may pick up loud background noise on threshold 0.024 (adjust if needed)
- No GUI - all configuration via code editing
- Limited to one language at a time (FR or ZH, not both)

---

## Future Roadmap

- [ ] Config file support (avoid hardcoding)
- [ ] Multi-language simultaneous subtitles
- [ ] Web dashboard
- [ ] Docker container
- [ ] Better VAD (webrtcvad library)
- [ ] Translation quality metrics
- [ ] More language support
- [ ] Performance profiling

---

For updates, visit: https://github.com/karlittoSR/StreamTranslation
