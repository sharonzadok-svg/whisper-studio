# Architecture: Subtitle Studio

Professional architecture documentation for developers and contributors.

## Overview

Subtitle Studio is a desktop application for subtitle editing and video rendering with offline Hebrew transcription. The application follows **clean architecture** principles with clear separation of concerns.

```
┌─────────────────────────────────────────┐
│        UI Layer (Tkinter)               │
│    subtitle_studio.py                   │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
┌───────▼────────┐   ┌──────────────────────┐
│ Media Service  │   │ Transcription Service│
│ (MP4 Rendering)│   │ (Hebrew STT)         │
└────────────────┘   └──────────────────────┘
        │                      │
        └──────────┬───────────┘
                   │
        ┌──────────▼────────────┐
        │  External Dependencies │
        │ FFmpeg, faster_whisper│
        │ CTranslate2, HF Hub   │
        └───────────────────────┘
```

---

## Directory Structure

```
whisper-studio/
├── desktop_app/                      # Main application package
│   ├── __init__.py                   # Package initialization
│   ├── subtitle_studio.py            # UI & orchestration (main window)
│   ├── media_service.py              # MP4 rendering & styling
│   └── transcription_service.py      # Hebrew speech-to-text
├── subtitle_studio_launcher.py       # PyInstaller entry point (CRITICAL)
├── tools/                            # Developer utilities (reusable)
├── models/                           # LLM model directory (NOT in git)
│   └── ivrit-whisper/               # Downloaded Ivrit model
├── videos/                           # Test projects & sample data
├── build/                            # PyInstaller build artifacts (NOT in git)
│   └── pyinstaller/
│       └── SubtitleStudio.spec      # Build configuration
├── release/                          # Portable executable (NOT in git)
│   └── SubtitleStudio/
│       ├── SubtitleStudio.exe       # Main application
│       └── _internal/               # Bundled dependencies
├── .venv/                            # Virtual environment (NOT in git)
├── .gitignore                        # Repository exclusions
├── requirements.txt                  # Python dependencies
├── requirements-gpu.txt              # GPU optimization (optional)
├── README.md                         # User documentation
├── SETUP.md                          # Setup instructions
├── CONTRIBUTING.md                   # Contributor guidelines
├── ARCHITECTURE.md                   # This file
└── .env.example                      # Environment variable template
```

---

## Core Modules

### 1. Desktop App Package (`desktop_app/`)

**Purpose**: Main application logic, orchestration, and UI

#### `subtitle_studio.py` – Main Window & Orchestration

**Responsibilities**:
- Initialize Tkinter UI window
- Manage application state (fonts, sizing, styling)
- Orchestrate workflows (render, transcribe)
- Handle user interactions (button clicks, file dialogs)
- Display status and progress to user

**Key Classes**:
```python
class SubtitleStudio(tk.Tk):
    """Main application window"""
    - __init__()        # Initialize UI
    - open_project()    # Load project folder
    - _render_worker()  # Render workflow (separate thread)
    - _transcribe_worker()  # Transcription workflow (separate thread)
```

**Key Methods**:
- `open_project()` – File dialog to select project folder
- `_render_worker()` – Thread-safe rendering without transcription
- `_transcribe_worker()` – Thread-safe Hebrew transcription
- `_update_status()` – Update UI status display
- `_update_progress()` – Update progress bar

**State Variables**:
- `font_name`, `font_size` – Subtitle styling
- `placement` – Subtitle position (Bottom, Middle, Custom)
- `offset_pixels` – Vertical offset adjustment
- `project_path`, `source_file`, `subtitle_file` – Current project

**Threading Model**:
- UI thread: Tkinter event loop
- Render thread: Media encoding (expensive, blocking)
- Transcription thread: Speech-to-text inference (expensive, blocking)
- Long operations run in separate threads to prevent UI freezing

---

#### `media_service.py` – MP4 Rendering

**Responsibilities**:
- Render MP4 with embedded subtitles
- Apply font, size, placement, and styling
- Validate project structure
- Handle FFmpeg integration

**Key Components**:
```python
@dataclass
class RenderStyle:
    """Immutable style configuration"""
    font_name: str           # e.g., "Arial"
    font_size: int          # e.g., 24
    placement: str          # "Bottom", "Middle", "Custom"
    offset_pixels: int      # Vertical offset

def validate_project(path: str) -> None:
    """Verify required files exist"""
    # Raises FileNotFoundError if source.mp4 or subtitles.en.srt missing

def render(source: str, srt: str, output: str, style: RenderStyle) -> None:
    """Main rendering function"""
    # Builds FFmpeg command with styling
    # Runs ffmpeg.exe subprocess
    # Raises MediaError on failure
```

**FFmpeg Integration**:
- Builds complex FFmpeg filter command
- Applies font styling via drawtext filter
- Handles SRT subtitle embedding
- Validates FFmpeg availability before use

**Error Handling**:
- Fail-fast: Explicit MediaError with actionable messages
- No silent defaults or fallbacks
- Clear logging of FFmpeg command and errors

---

#### `transcription_service.py` – Hebrew Speech-to-Text

**Responsibilities**:
- Run offline Hebrew transcription
- Manage Ivrit Whisper model
- Generate SRT subtitle files
- Report progress and timing

**Key Functions**:
```python
def transcribe_hebrew(source: str, project_folder: str) -> Tuple[int, float]:
    """
    Transcribe Hebrew audio from MP4
    
    Args:
        source: Path to source MP4
        project_folder: Output folder for subtitles.he.srt
    
    Returns:
        (segment_count, elapsed_seconds)
    
    Raises:
        TranscriptionError: Model not found or inference failed
    """
```

**Model Management**:
- Uses CTranslate2 for efficient inference
- Looks for model at: `./models/ivrit-whisper/`
- Fail-fast: Explicit error if model missing
- No automatic download or fallback

**SRT Generation**:
- Writes structured SRT format (index, timestamp, text)
- UTF-8 encoding
- Segment timing derived from Whisper output

**Performance Characteristics**:
- ~30-60 seconds per minute of audio (CPU)
- ~3-5 seconds per minute of audio (GPU with CUDA)
- Single-threaded inference

---

### 2. Entry Point (`subtitle_studio_launcher.py`)

**Purpose**: Package-aware PyInstaller entry point

**Critical for**: Ensuring PyInstaller preserves desktop_app as a loadable package

```python
from desktop_app.subtitle_studio import main
if __name__ == "__main__":
    main()
```

**Why Critical**:
- Direct script execution → loose modules → import errors
- Launcher pattern → preserves package structure → fixed imports
- Without launcher: `ModuleNotFoundError: No module named 'media_service'`

**PyInstaller Configuration**:
```
Entry script: subtitle_studio_launcher.py (not subtitle_studio.py)
```

---

## Design Patterns

### 1. Separation of Concerns

**UI Layer** (subtitle_studio.py)
- Tkinter window and widgets
- User interaction handling
- State management (fonts, sizing)

**Service Layer** (media_service.py, transcription_service.py)
- Business logic (rendering, transcription)
- External integration (FFmpeg, Hugging Face)
- Error handling and validation

**Benefit**: Changes to FFmpeg or models don't require UI changes.

---

### 2. Workflow Separation

**Design Goal**: Fast styling iteration without re-transcribing

**Render Workflow** (cheap, fast):
1. Load existing English SRT
2. Apply styling (font, size, placement)
3. Re-encode MP4 with styled subtitles
4. ✅ Complete in 10-60 seconds

**Transcription Workflow** (expensive, slow):
1. Extract audio from MP4
2. Run Hebrew speech-to-text inference
3. Generate new subtitles.he.srt
4. ⏱️ Takes 30-60 seconds per minute of audio (CPU)

**Implementation**:
- Separate service modules (media_service.py, transcription_service.py)
- Separate worker threads (_render_worker, _transcribe_worker)
- Separate UI buttons and status messages
- User explicitly chooses workflow

---

### 3. Fail-Fast Error Handling

**Principle**: Never silently use defaults or fallbacks

**Examples**:

```python
# ✅ GOOD: Explicit, actionable error
def validate_project(path: str) -> None:
    if not Path(source_file).exists():
        raise FileNotFoundError(
            f"Project missing required file: source.mp4\n"
            f"Looked in: {path}\n"
            f"Expected: {source_file}"
        )

# ❌ BAD: Silent fallback
def get_font_size() -> int:
    # If config missing, use 24 (user doesn't know why!)
    return config.get('font_size', 24)
```

**Benefits**:
- Users know exactly what's wrong
- Easy to fix errors
- No mysterious misbehavior

---

### 4. Threading for UI Responsiveness

**Model**:
```
Main UI Thread (Tkinter event loop)
    ├─ Listens for button clicks
    ├─ Updates widgets (labels, progress bar)
    └─ Spawns worker threads for long tasks

Render Thread (media_service.render)
    └─ Blocks on FFmpeg encoding (✅ safe, won't freeze UI)

Transcription Thread (transcription_service.transcribe_hebrew)
    └─ Blocks on model inference (✅ safe, won't freeze UI)
```

**Thread-Safe Queue Communication**:
- UI sends work to queue
- Worker thread processes
- Worker sends result back via queue
- UI updates when result arrives

---

## External Dependencies

### Python Packages

| Package | Purpose | Version |
|---------|---------|---------|
| Tkinter | GUI framework | bundled |
| faster-whisper | Whisper inference wrapper | 1.0.3+ |
| CTranslate2 | Fast model inference | 4.5.0+ |
| ffmpeg-python | FFmpeg subprocess wrapper | 0.2.1+ |
| huggingface-hub | Model download & auth | 0.23.5+ |

### External Binaries

| Binary | Purpose | Source |
|--------|---------|--------|
| ffmpeg.exe | Video encoding | Gyan.FFmpeg.Shared |
| ffprobe.exe | Video metadata | Gyan.FFmpeg.Shared |

### ML Models (Bundled in Release, NOT in Git)

| Model | Purpose | Source | Size |
|-------|---------|--------|------|
| Ivrit Whisper | Hebrew speech-to-text | HuggingFace ivrit-ai | ~1.5 GB |

---

## Data Flow

### Render Workflow

```
1. User clicks "Apply Font & Re-render MP4"
   │
2. UI validates project (source.mp4 + subtitles.en.srt)
   │
3. Create RenderStyle from UI inputs
   │
4. Spawn render_worker thread:
   │  ├─ Call media_service.render(source, srt, output, style)
   │  ├─ Build FFmpeg command with styling filters
   │  ├─ Run ffmpeg.exe subprocess
   │  ├─ Poll progress and update queue
   │  └─ Send result/error back to UI via queue
   │
5. UI receives result:
   ├─ Success → Display "Rendered: output.en.mp4"
   └─ Error → Display error message with remediation steps
```

### Transcription Workflow

```
1. User clicks "Create Hebrew Transcript"
   │
2. UI validates project (source.mp4 exists)
   │
3. Spawn transcription_worker thread:
   │  ├─ Load Ivrit model from ./models/ivrit-whisper/
   │  ├─ Extract audio from source.mp4
   │  ├─ Run faster_whisper.transcribe(audio, model)
   │  ├─ Generate subtitles.he.srt
   │  ├─ Poll progress and update queue
   │  └─ Send segment_count + elapsed_time to UI
   │
4. UI receives result:
   ├─ Success → Display "Transcribed: 250 segments in 45 seconds"
   └─ Error → Display model/inference error with setup guidance
```

---

## Configuration & Secrets

### Environment Variables (Optional)

See `.env.example` for all available options.

**FFmpeg Paths**:
- Auto-detected from PATH by default
- Override with `FFMPEG_PATH` / `FFPROBE_PATH` if custom installation

**Model Directory**:
- Default: `./models` (project root)
- Override with `MODELS_DIR` if alternative location

**Hugging Face Authentication**:
- Use `huggingface-cli login` (not environment variables)
- Credentials stored securely in `~/.cache/huggingface/`

### Secrets Management

❌ **Never**:
- Hardcode API keys, passwords, or tokens in code
- Commit `.env` files to git
- Log sensitive data

✅ **Always**:
- Use environment variables or config files
- Add to `.gitignore`
- Use `.env.example` as template
- Fail-fast if required config is missing

---

## Deployment

### Source Distribution (Development)

```bash
git clone <repo>
cd whisper-studio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m desktop_app.subtitle_studio
```

### Standalone Executable (Distribution)

See the [build instructions](README.md#building-standalone-executable). The local output is `release/SubtitleStudio/SubtitleStudio.exe`; it is not tracked in Git.

### Model Distribution

❌ **NOT** included in executable or git repository

✅ **Downloaded separately** by users:
```bash
huggingface-cli download ivrit-ai/whisper-ivrit --local-dir ./models/ivrit-whisper
```

---

## Performance Considerations

### Rendering (MP4 Encoding)

**Bottleneck**: FFmpeg video encoding
- Single-threaded by default
- Can be parallelized with FFmpeg options if needed
- Speed depends on: codec, resolution, bitrate

**Optimization**:
- Use hardware encoding if available (`-c:v h264_nvenc` for NVIDIA)
- Adjust bitrate vs. quality trade-off
- Pre-process subtitles to reduce render count

### Transcription (Speech-to-Text)

**Bottleneck**: ML model inference (CPU/GPU)

**CPU Performance**:
- ~30-60 seconds per minute of audio
- Depends on processor speed
- Single-threaded inference

**GPU Acceleration**:
- ~3-5 seconds per minute of audio (NVIDIA CUDA)
- Requires `torch[cuda]` and compatible GPU
- 10x+ speedup

**Optimization**:
- Use GPU if available (see `requirements-gpu.txt`)
- Batch processing for multiple files (future enhancement)
- Model quantization (future enhancement)

---

## Testing

### Unit Tests (Recommended Practice)

Example structure:
```
tests/
├── test_media_service.py
├── test_transcription_service.py
└── test_subtitle_studio.py
```

### Manual Testing Workflow

1. **Render Test**:
   - Create project folder with source.mp4 + subtitles.en.srt
   - Change font/size
   - Click render
   - Verify output.en.mp4 generated with new styling

2. **Transcription Test**:
   - Open project folder
   - Click "Create Hebrew Transcript"
   - Verify subtitles.he.srt generated
   - Check segment count and timing

3. **Error Handling**:
   - Delete source.mp4 → render should fail with clear message
   - Move model folder → transcribe should fail with clear message
   - Use malformed SRT → render should handle gracefully

---

## Contributing Guidelines

### Code Standards
- PEP 8 style compliance
- Type hints on all functions
- Docstrings on classes and public methods
- No magic numbers (use named constants)

### Adding Features
1. Create feature branch
2. Make changes in appropriate module
3. Test locally with clean venv
4. Update README/SETUP if needed
5. Submit PR with clear description

### Before Submitting PR
- ✅ Code runs without errors
- ✅ No model files committed
- ✅ No hardcoded paths or credentials
- ✅ Clear error messages for failures
- ✅ No unnecessary dependencies added

---

## Future Enhancements

**Potential Improvements**:
- Batch transcription (multiple files)
- GPU acceleration documentation
- Model quantization for faster inference
- Subtitle merging (EN + HE side-by-side)
- Custom subtitle styling (colors, shadows)
- Batch rendering with presets
- Unit test suite with pytest
- CI/CD pipeline with GitHub Actions
- Auto-update mechanism for releases

---

## References

- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html
- **Tkinter Guide**: https://docs.python.org/3/library/tkinter.html
- **faster-whisper**: https://github.com/guillaumekln/faster-whisper
- **Ivrit Whisper Model**: https://huggingface.co/ivrit-ai/whisper-ivrit
- **Python Virtual Environments**: https://docs.python.org/3/tutorial/venv.html

---

**Last Updated**: 2024  
**Architecture Version**: 1.0  
**Status**: Production Ready
