# Subtitle Studio

Professional subtitle editor and multilingual transcription tool. Edit timed SRT subtitles, render styled MP4 videos, and generate Hebrew transcripts from audio—all offline with speech-to-text technology powered by Whisper.

## Features

- **SRT Subtitle Editor**: Edit and manage subtitle timing and content
- **MP4 Rendering**: Embed styled subtitles into video files
- **Offline Hebrew Transcription**: Generate Hebrew transcripts from video audio without internet dependency
- **Font & Style Control**: Customize subtitle appearance (font, size, placement, offset)
- **Workflow Separation**: Apply styling changes without re-running expensive transcription
- **Standalone Executable**: Distribute and run as a portable Windows application

## System Requirements

- **OS**: Windows 10/11
- **Python** (for development): 3.11.9+
- **RAM**: 4 GB minimum (8 GB recommended for transcription)
- **Disk Space**: 2 GB+ for model files and FFmpeg

---

## Quick Start (Executable)

### Download Release

If a portable ZIP has been published, download it from the [Releases](../../releases) page. The executable is not stored in Git; to run a clone locally, follow [Clone & Install](#clone--install) instead.

### First Run

1. Extract `SubtitleStudio-portable.zip` to your desired location
2. Run `SubtitleStudio.exe` directly

The Hebrew transcription feature also requires the Ivrit model; see [Model Setup](#model-setup).

---

## Development Setup

### Prerequisites

1. **Python 3.11.9**
   ```powershell
   # Verify installation
   python --version
   ```

2. **FFmpeg**
   ```powershell
   # Install via WinGet
   winget install Gyan.FFmpeg.Shared
   ```

3. **Hugging Face Model (Ivrit Hebrew Transcription)**
   - Download from: https://huggingface.co/ivrit-ai/whisper-ivrit
   - See [Model Setup](#model-setup) below for detailed instructions

### Clone & Install

```powershell
# Clone repository
git clone https://github.com/sharonzadok-svg/whisper-studio.git
cd whisper-studio

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Run Application

```powershell
# From project root (with virtual environment activated)
python -m desktop_app.subtitle_studio
```

---

## Model Setup

### Download Ivrit Whisper Model

The Hebrew transcription feature requires the **Ivrit Whisper model** from Hugging Face. This model is **NOT** included in the repository—only the application code is versioned.

#### Step 1: Create Hugging Face Account

1. Visit https://huggingface.co
2. Click **Sign Up** and create an account
3. Verify your email

#### Step 2: Authenticate Locally

```powershell
# Install Hugging Face CLI (if not already installed)
pip install huggingface-hub

# Login to Hugging Face
huggingface-cli login
```

When prompted, enter your Hugging Face API token:
- Go to https://huggingface.co/settings/tokens
- Create a new token (read access is sufficient)
- Paste the token into the terminal and press Enter

#### Step 3: Download Model

Create a `models` directory in the project root and download:

```powershell
# Create models directory
New-Item -ItemType Directory -Path "models" -Force

# Download Ivrit model
huggingface-cli download ivrit-ai/whisper-ivrit --local-dir ./models/ivrit-whisper
```

This downloads approximately **1.5 GB** of model files. The download is one-time only.

#### Step 4: Verify Installation

After download, verify the model files exist:
```powershell
ls models/ivrit-whisper/
# Should contain: model.bin, config.json, etc.
```

---

## Project Structure

```
whisper-studio/
├── desktop_app/              # Main application package
│   ├── subtitle_studio.py    # Main UI window
│   ├── media_service.py      # MP4 rendering & styling
│   ├── transcription_service.py  # Hebrew transcription
│   └── __init__.py
├── subtitle_studio_launcher.py  # Portable executable entry point
├── tools/                    # Developer utilities
├── videos/                   # Project folders (for testing)
├── models/                   # LLM model files (NOT in git)
│   └── ivrit-whisper/        # Downloaded Ivrit model
├── requirements.txt          # Python dependencies
├── .gitignore               # Excludes models, builds, cache
└── README.md                # This file
```

---

## Git & Repository Management

### What's in Git

✅ **Include in version control:**
- Application source code (`desktop_app/`)
- Configuration files (`requirements.txt`, `.gitignore`)
- Documentation (`README.md`)
- Development utilities (`tools/`)

### What's Excluded from Git

❌ **NOT in version control:**
- **Model files** (`models/` directory) — downloaded separately
- **Build artifacts** (`build/`, `release/`)
- **Cache & runtime** (`__pycache__/`, `.venv/`)
- **Local video projects** (`videos/` except `videos/README.md`)
- **Salesforce CLI cache** (`.sf/`)
- **IDE settings** (`.vscode/`, `.idea/`)

### .gitignore Configuration

The `.gitignore` file automatically excludes:
```
# Large model files
models/
*.bin

# Build & packaging
build/
release/
*.spec

# Python
__pycache__/
*.pyc
.venv/
dist/

# Local data
videos/*
!videos/README.md
.sf/
```

---

## Workflow

### Render Existing Subtitles (No Re-transcription)

1. Open a project folder containing:
   - `source.mp4` – video file
   - `subtitles.en.srt` – English subtitle file

2. Adjust styling:
   - Change **Font** (e.g., Arial, Courier)
   - Adjust **Font Size** (e.g., 24pt)
   - Set **Placement** (Bottom, Middle, Custom)
   - Add **Offset** (vertical pixel adjustment)

3. Click **"Apply Font & Re-render MP4"**
   - Generates `output.en.mp4` with new styling
   - **Does NOT** re-run transcription

### Generate Hebrew Transcript

1. Open a project folder with `source.mp4`
2. Click **"Create Hebrew Transcript"**
   - Runs offline Hebrew speech-to-text
   - Generates `subtitles.he.srt` in project folder
   - Displays segment count and processing time

**This step requires the Ivrit model** (see [Model Setup](#model-setup))

---

## Building Standalone Executable

For distribution as a portable `.exe` without requiring Python installation:

```powershell
# Install PyInstaller
pip install PyInstaller

# Build from project root
python -m PyInstaller `
  --noconfirm `
  --onedir `
  --windowed `
   --name SubtitleStudio `
  --distpath release `
  --collect-all faster_whisper `
  --collect-all ctranslate2 `
  --add-binary "C:\path\to\ffmpeg.exe;ffmpeg" `
  --add-binary "C:\path\to\ffprobe.exe;ffmpeg" `
  subtitle_studio_launcher.py
```

Output: `release/SubtitleStudio/SubtitleStudio.exe` (local build; not committed to Git).

### Portable Distribution

To distribute as a ZIP archive:

```powershell
# Compress release folder
Compress-Archive -Path release/SubtitleStudio -DestinationPath SubtitleStudio-portable.zip
```

**Note:** This build command does not include the model files. For Hebrew transcription, download the model (see [Model Setup](#model-setup)) and place it in `release/SubtitleStudio/_internal/models/ivrit-whisper` before making the ZIP.

---

## Troubleshooting

### Import Errors on Launch

**Problem**: `ModuleNotFoundError: No module named 'desktop_app'`

**Solution**: Ensure you're running from the project root:
```powershell
cd whisper-studio
python -m desktop_app.subtitle_studio
```

### FFmpeg Not Found

**Problem**: "FFmpeg executable not found"

**Solution**:
```powershell
# Reinstall FFmpeg
winget install Gyan.FFmpeg.Shared
# Verify installation
ffmpeg -version
```

### Model Download Fails

**Problem**: "Permission denied" or "Connection timeout"

**Solution**:
1. Check internet connection
2. Verify Hugging Face token: `huggingface-cli whoami`
3. Try downloading with verbose output:
   ```powershell
   huggingface-cli download ivrit-ai/whisper-ivrit --local-dir ./models/ivrit-whisper --verbose
   ```

### Transcription Very Slow

**Problem**: Hebrew transcription takes > 2 minutes per minute of audio

**Solution**:
- This is expected on CPUs. For 10x+ speedup, use GPU:
  - NVIDIA GPU: Install `torch-cuda` variant
  - See `requirements-gpu.txt` for GPU setup

---

## Dependencies

Key Python packages (see `requirements.txt`):
- **Tkinter** – GUI framework (bundled with Python)
- **faster-whisper** – Speech-to-text inference
- **CTranslate2** – Efficient model inference engine
- **ffmpeg-python** – Video processing

---

## License

[Specify your license here, e.g., MIT, Apache 2.0, etc.]

## Support

For issues, questions, or contributions:
- Open an [Issue](../../issues)
- Submit a [Pull Request](../../pulls)
- Contact: [your-contact-info]

---

## Professional Standards

This project follows enterprise software engineering practices:
- Clean architecture with separation of concerns
- Fail-fast error handling with actionable messages
- No hardcoded credentials or configuration
- Comprehensive documentation for setup and deployment
- Proper dependency isolation using Python virtual environments
- Model files managed separately to keep repository lean
