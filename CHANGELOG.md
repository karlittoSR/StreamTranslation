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

## [1.1.0] - Planned

- Config file loading (YAML/JSON support)
- Multiple subtitle tracks (FR + EN side-by-side display)
- Performance improvements (VAD optimization)
- WebRTC VAD integration (better speech detection)
- Metrics dashboard
- Docker support

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
