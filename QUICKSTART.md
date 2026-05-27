# ⚡ Quick Start Guide

## 5-Minute Setup

### 1. Get API Keys (2 min)

**OpenAI:**
- Go to https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy the key

**DeepL:**
- Go to https://www.deepl.com/pro/account
- Sign up (free, no credit card)
- Go to "API keys"
- Copy your Free API key

**Azure (optional):**
- Only needed if DeepL quota runs out
- Can skip for now

### 2. Clone & Setup (2 min)

```powershell
# Open PowerShell in StreamTranslation folder
cd C:\Users\YourName\source\repos\StreamTranslation

# Run setup script
.\setup.ps1

# Activate environment (if not already active)
.\venv\Scripts\Activate.ps1
```

### 3. Add API Keys (1 min)

```powershell
notepad .env
```

Paste:
```
OPENAI_API_KEY=sk-your-openai-key
DEEPL_AUTH_KEY=your-deepl-key
AZURE_AUTH_KEY=skip-for-now
```

Save and close.

### 4. Configure Language (Optional)

**For French speakers:**
- Nothing to change - it's already configured for French

**For Chinese speakers:**
Edit `live_subs.py`:

Find this line in `transcribe_audio()` function (around line 600):
```python
language="fr",
```

Change to:
```python
language="zh",
```

Also update the transcription prompt in Config (around line 40) to something like:
```python
transcription_prompt: str = (
	"You are transcribing Chinese gaming speech from a live stream. "
	"Remove filler words. If unclear, leave blank."
)
```

### 5. Find Your Microphone

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

You'll see:
```
  0 - Speakers
  1 - Microphone (your input device)
  2 - Headset
```

**Note the number of your microphone.**

Edit `live_subs.py` line ~38:
```python
input_device_index: int = 1  # Change to your microphone number
```

### 6. Setup OBS

1. OBS → Add Source → **Text (GDI+)**
2. Name: `Subtitles`
3. **Check "Read from file"**
4. **Browse** → Select `subs_en.txt`
5. Set font size: `32-48pt`
6. Position: bottom center
7. **OK**

### 7. Test It!

```powershell
python live_subs.py
```

You should see:
```
🎤 Starting live subtitle transcription
   Device: 1, Sample rate: 16000 Hz
   🌍 DeepL translation enabled -> EN-US
```

**Speak into your microphone!**

After 2 seconds of silence, you'll see:
- Console shows: `FR: Bonjour [EN: Hello]`
- OBS shows: `Hello`

Press `Ctrl+C` to stop.

---

## Troubleshooting

**"No module named openai"?**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade
```

**"DEEPL_AUTH_KEY not set"?**
- Did you create `.env` file (not just `.env.example`)?
- Did you add your actual key to `.env`?
- Restart PowerShell

**No audio detected?**
```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```
Then update `input_device_index` to correct number.

**Subtitles not in OBS?**
- Text source: check "Read from file" is ✓
- Check path to `subs_en.txt` is correct
- Restart OBS

**Wrong language being transcribed?**
- For Chinese: change `language="fr"` to `language="zh"` in `transcribe_audio()`
- For other languages: change `language="fr"` to your language code

---

## Daily Usage

Once setup is done:

```powershell
cd C:\Users\YourName\source\repos\StreamTranslation
.\venv\Scripts\Activate.ps1
python live_subs.py
```

Start streaming in OBS - subtitles appear automatically!

---

## Cost Summary

| Service | Cost/Month |
|---------|-----------|
| OpenAI | ~$12 |
| DeepL | $0 (free tier) |
| Azure | $0 (only if needed) |
| **Total** | **~$12** |

Very affordable for a professional setup!

---

## What's Next?

- See `README.md` for detailed configuration options
- Create `glossary.json` to fix common mistranslations
- Adjust `vad_energy_threshold` if picking up background noise
- Customize colors/fonts in OBS text source

---

**Happy streaming!** 🚀
