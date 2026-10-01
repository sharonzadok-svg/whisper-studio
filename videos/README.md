# Editable video folders

```text
videos/
  video-name/
    source.mp4          subtitle-free source; never overwrite this file
    subtitles.en.srt    business-editable English text and timing
    output.en.mp4       generated file; replace after every SRT update
    transcript.he.json  optional timestamped Hebrew transcription record
```

After changing `subtitles.en.srt`, regenerate one video:

```powershell
& "C:\Users\szadok\AppData\Local\Programs\Python\Python311\python.exe" tools\render_videos.py videos\video-name
```

When the source already has Hebrew captions burned into its bottom area, place English below it:

```powershell
& "C:\Users\szadok\AppData\Local\Programs\Python\Python311\python.exe" tools\render_videos.py videos\video-name --font-size 10
```

Regenerate every folder that has both `source.mp4` and `subtitles.en.srt`:

```powershell
& "C:\Users\szadok\AppData\Local\Programs\Python\Python311\python.exe" tools\render_videos.py --all
```

The renderer validates every SRT cue against the source duration before it burns subtitles. It will not replace an output MP4 when the source or SRT is missing or a cue is invalid.