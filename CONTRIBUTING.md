# Contributing to Subtitle Studio

Thank you for your interest in contributing! This guide outlines best practices for submitting code changes.

## Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Make changes** following [Code Standards](#code-standards)
4. **Test** locally with your changes
5. **Commit** with clear messages: `git commit -m "Add feature: description"`
6. **Push** to your fork: `git push origin feature/your-feature-name`
7. **Submit** a Pull Request with description of changes

## Code Standards

### Python Style

- Follow **PEP 8** conventions
- Use **type hints** for function parameters and returns
- Avoid code duplication; extract to utility functions
- Add docstrings to classes and public methods

Example:
```python
def render(source: str, srt: str, output: str, style: RenderStyle) -> None:
    """
    Render MP4 with embedded subtitles.
    
    Args:
        source: Path to source MP4 file
        srt: Path to SRT subtitle file
        output: Path for output MP4
        style: Subtitle styling configuration
    
    Raises:
        FileNotFoundError: If source or SRT files don't exist
        RenderError: If FFmpeg rendering fails
    """
```

### Separation of Concerns

- **UI Logic** → `desktop_app/subtitle_studio.py`
- **Media Rendering** → `desktop_app/media_service.py`
- **Transcription** → `desktop_app/transcription_service.py`
- **Utilities** → `tools/` (reusable developer utilities)

### Configuration & Secrets

- ❌ Never hardcode credentials, API keys, or paths
- ✅ Use environment variables or config files
- ✅ Add defaults with fail-fast error messages

### Testing

- Test locally before submitting PR
- Include steps to verify your changes
- Test on clean system (fresh venv) if possible

## Repository Guidelines

### What's in Git

✅ Python source code  
✅ Configuration files  
✅ Documentation  
✅ Developer tools  

### What's NOT in Git

❌ Model files (`models/`)  
❌ Build artifacts (`build/`, `release/`)  
❌ Video test files (use `.gitignore`)  
❌ Virtual environments (`.venv/`)  

### Commits

- Make logical, atomic commits
- Use clear, descriptive messages
- Reference issues: "Fixes #123" or "Closes #456"

Example:
```
feat: Add Hebrew language subtitle export

- Export subtitles to Hebrew SRT format
- Support encoding in Windows-1252 and UTF-8
- Fixes #42
```

## Pull Request Process

1. **Update** README.md if you add features
2. **Write** clear PR description:
   - What problem does this solve?
   - How was it tested?
   - Any breaking changes?
3. **Link** related issues: "Closes #123"
4. **Request review** from project maintainers
5. **Respond** to feedback promptly

## No Model Files

⚠️ **Important**: Do NOT commit model files or large binaries.

If your changes reference models:
1. Add to `.gitignore` if not already there
2. Document download process in SETUP.md
3. Ensure CI/CD doesn't cache large files

## Questions?

- Open a GitHub Discussion
- Comment on related Issues
- Check existing documentation

---

Thank you for contributing to Whisper Studio! 🎬
