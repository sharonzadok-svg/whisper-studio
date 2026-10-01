# Setup Guide: Subtitle Studio

Complete step-by-step guide for first-time setup and configuration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Environment Setup](#development-environment-setup)
3. [Model Download & Configuration](#model-download--configuration)
4. [Verify Installation](#verify-installation)
5. [First Run](#first-run)

---

## Prerequisites

### Windows System Requirements

- **OS**: Windows 10 Build 19041+ or Windows 11
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk Space**: 4 GB for application + dependencies + models
- **Internet**: Required for initial model download (1.5 GB)

### Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11.9+ | Runtime environment |
| FFmpeg | 7.0+ | Video processing |
| Git | 2.40+ | Version control (optional) |

---

## Development Environment Setup

### Step 1: Install Python 3.11.9

**Option A: Using Windows Installer**

1. Download from https://www.python.org/downloads/ (version 3.11.9)
2. Run installer
3. ✅ **CHECK**: "Add python.exe to PATH"
4. Click "Install Now"
5. Verify:
   ```powershell
   python --version
   # Output: Python 3.11.9
   ```

**Option B: Using Windows Package Manager**

```powershell
winget install Python.Python.3.11
```

### Step 2: Install FFmpeg

```powershell
# Using Windows Package Manager (recommended)
winget install Gyan.FFmpeg.Shared

# Verify installation
ffmpeg -version
ffprobe -version
```

### Step 3: Clone Repository

```powershell
# Navigate to your workspace
cd C:\Workspace

# Clone the repository
git clone https://github.com/sharonzadok-svg/whisper-studio.git
cd whisper-studio
```

### Step 4: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# You should see (.venv) in your prompt
```

### Step 5: Install Python Dependencies

```powershell
# Ensure you're in the virtual environment (.venv should be active)
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

---

## Model Download & Configuration

### What is the Ivrit Model?

The **Ivrit Whisper Model** is a Hebrew language speech-to-text model optimized for modern Hebrew. It's hosted on Hugging Face (https://huggingface.co/ivrit-ai/whisper-ivrit) and must be downloaded separately.

**Why separate from code?**
- Model files are ~1.5 GB (too large for git repositories)
- Allows fast code updates without re-downloading models
- Professional practice for ML applications

---

### Step 1: Create Hugging Face Account

1. Navigate to https://huggingface.co
2. Click **Sign Up** (top right)
3. Fill in registration form:
   - Email
   - Username
   - Password
4. Verify email address
5. Complete profile (optional but recommended)

---

### Step 2: Get Hugging Face API Token

1. Log in to Hugging Face
2. Go to **Settings** → **Access Tokens** (https://huggingface.co/settings/tokens)
3. Click **New token**
   - Name: `SubtitleStudio` (or any name)
   - Role: **Read** (sufficient access level)
   - Click **Create token**
4. Copy the token (starts with `hf_`)

**⚠️ SECURITY**: Never commit tokens to git or share publicly.

---

### Step 3: Authenticate Hugging Face CLI

```powershell
# Ensure virtual environment is active (.venv)

# Install huggingface-hub if needed
pip install huggingface-hub

# Authenticate
huggingface-cli login
```

When prompted:
```
    _|    _|  _|    _|    _|_|_|    _|_|_|  _|_|_|  _|      _|
    _|    _|  _|    _|  _|        _|          _|    _|_|    _|
    _|    _|  _|    _|  _|        _|          _|    _|  _|  _|
    _|    _|  _|    _|  _|        _|          _|    _|    _|_|
    _|      _|_|      _|  _|_|_|    _|_|_|  _|    _|      _|

    To authenticate, you need a token. Visit
    https://huggingface.co/settings/tokens to create one.

Token (will not be echoed):
```

Paste your token and press **Enter**.

**Verify authentication:**
```powershell
huggingface-cli whoami
# Output: username (your HF username)
```

---

### Step 4: Download Ivrit Model

```powershell
# Create models directory in project root
New-Item -ItemType Directory -Path models -Force

# Download model to local directory
huggingface-cli download ivrit-ai/whisper-ivrit `
    --local-dir ./models/ivrit-whisper `
    --repo-type model
```

**Expected output:**
```
Downloading [████████████████████████████] 1.5GB/1.5GB
```

**Download time**: 5-30 minutes depending on internet speed.

---

### Step 5: Verify Model Files

```powershell
# List downloaded files
ls -la models/ivrit-whisper/

# Should contain:
# - model.bin (largest file, ~1.4 GB)
# - config.json
# - preprocessor_config.json
# - tokenizer.json
# - model.safetensors (alternative format)
# - README.md
```

---

## Verify Installation

Run this verification script to ensure everything is set up correctly:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Check Python
Write-Host "Python:" -ForegroundColor Green
python --version

# Check FFmpeg
Write-Host "FFmpeg:" -ForegroundColor Green
ffmpeg -version

# Check dependencies
Write-Host "Dependencies:" -ForegroundColor Green
pip list | Select-Object -First 20

# Check model
Write-Host "Model:" -ForegroundColor Green
ls models/ivrit-whisper/ | Select-Object Name

# Check Hugging Face authentication
Write-Host "Hugging Face Auth:" -ForegroundColor Green
huggingface-cli whoami
```

All checks should pass with ✅ status.

---

## First Run

### Launch Application

```powershell
# From project root (virtual environment must be active)
python -m desktop_app.subtitle_studio
```

**Expected behavior:**
1. Tkinter window opens
2. Application title: "Subtitle Studio"
3. Buttons visible: "Open Project", "Apply Font & Re-render MP4", "Create Hebrew Transcript"
4. Help text displays workflow instructions

### Test Rendering (Without Transcription)

1. Click **"Open Project"**
2. Navigate to `videos/` folder (or create test folder with):
   - `source.mp4` (any video file)
   - `subtitles.en.srt` (any SRT file)
3. Change **Font** or **Font Size**
4. Click **"Apply Font & Re-render MP4"**
   - Should complete in 10-60 seconds
   - Creates `output.en.mp4` in project folder

### Test Transcription (Hebrew Model)

1. Open a project with `source.mp4`
2. Click **"Create Hebrew Transcript"**
3. Monitor progress bar:
   - Processing should start within 5 seconds
   - ~30-60 seconds per minute of audio (CPU)
   - ~3-5 seconds per minute of audio (GPU)
4. Creates `subtitles.he.srt` when complete

---

## Troubleshooting First Setup

### Virtual Environment Not Activating

```powershell
# If .\.venv\Scripts\Activate.ps1 fails:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
.\.venv\Scripts\Activate.ps1
```

### FFmpeg Not Found

```powershell
# Reinstall FFmpeg
winget uninstall Gyan.FFmpeg.Shared
winget install Gyan.FFmpeg.Shared

# Add to PATH manually if needed:
# 1. Open System Properties
# 2. Environment Variables
# 3. Add FFmpeg bin folder to PATH
```

### Model Download Fails

**Error**: "Connection refused" or "Timeout"

```powershell
# Try with verbose output
huggingface-cli download ivrit-ai/whisper-ivrit `
    --local-dir ./models/ivrit-whisper `
    --repo-type model `
    --verbose

# If still failing, check:
huggingface-cli whoami  # Verify authentication
ipconfig               # Verify internet connectivity
```

### "Module not found" on Launch

```powershell
# Ensure virtual environment is active
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Next Steps

1. ✅ Environment set up
2. ✅ Model downloaded
3. ✅ Application verified

**Ready to use!** See [README.md](README.md) for workflow documentation.

---

## Additional Resources

- **Hugging Face Documentation**: https://huggingface.co/docs
- **Ivrit Model Page**: https://huggingface.co/ivrit-ai/whisper-ivrit
- **Python Virtual Environments**: https://docs.python.org/3/tutorial/venv.html
- **FFmpeg Installation**: https://ffmpeg.org/download.html

## Getting Help

- Check [README.md](README.md) Troubleshooting section
- Open an Issue on GitHub with:
  - Setup step where it failed
  - Full error message
  - Output from verification commands above
