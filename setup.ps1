# StreamTranslation Setup Script for Windows
# Run: .\setup.ps1

Write-Host "StreamTranslation Setup" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Green
python --version
if ($LASTEXITCODE -ne 0) {
	Write-Host "Python not found! Please install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Red
	exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv
if ($LASTEXITCODE -ne 0) {
	Write-Host "Failed to create virtual environment" -ForegroundColor Red
	exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
	Write-Host "Failed to install dependencies" -ForegroundColor Red
	exit 1
}

# Copy .env template
Write-Host "✓ Creating .env file..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
	Copy-Item ".env.example" ".env"
	Write-Host "  Created .env (edit with your API keys)" -ForegroundColor Yellow
} else {
	Write-Host "  .env already exists" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=========================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your API keys:" -ForegroundColor Gray
Write-Host "     notepad .env" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Find your microphone device:" -ForegroundColor Gray
Write-Host "     python -c \"import sounddevice as sd; print(sd.query_devices())\"" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Edit live_subs.py Config class:" -ForegroundColor Gray
Write-Host "     - Set input_device_index to your microphone" -ForegroundColor Yellow
Write-Host "     - Set deepl_target_lang to your target language" -ForegroundColor Yellow
Write-Host "     - Change language='fr' to language='zh' if using Chinese" -ForegroundColor Yellow
Write-Host ""
Write-Host "  4. Set up OBS:" -ForegroundColor Gray
Write-Host "     - Add Text source" -ForegroundColor Yellow
Write-Host "     - Check 'Read from file'" -ForegroundColor Yellow
Write-Host "     - Select subs_en.txt" -ForegroundColor Yellow
Write-Host ""
Write-Host "  5. Run the script:" -ForegroundColor Gray
Write-Host "     python live_subs.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "For detailed instructions, see README.md" -ForegroundColor Cyan
