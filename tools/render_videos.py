"""Render English-subtitled video folders.

Each editable folder must contain:
    source.mp4          source video with no burned-in subtitles
    subtitles.en.srt    editable English subtitles

The rendered result is always written to output.en.mp4.

Examples:
    python tools\render_videos.py videos\whatsapp-2026-09-29-103429
    python tools\render_videos.py videos\Hodi_in_war --font-size 10
    python tools\render_videos.py --all
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIDEOS_ROOT = PROJECT_ROOT / "videos"
BURN_TOOL = PROJECT_ROOT / "tools" / "burn_subtitles.py"


def render_folder(video_folder: Path, font_size: int | None) -> None:
    source = video_folder / "source.mp4"
    subtitles = video_folder / "subtitles.en.srt"
    output = video_folder / "output.en.mp4"
    missing = [path.name for path in (source, subtitles) if not path.is_file()]
    if missing:
        raise ValueError(f"{video_folder.name}: missing {', '.join(missing)}")

    print(f"Rendering {video_folder.name}")
    command = [sys.executable, str(BURN_TOOL), str(source), str(subtitles), str(output), "--overwrite"]
    if font_size is not None:
        command.extend(["--font-size", str(font_size)])
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_folder", type=Path, nargs="?", help="One editable video folder")
    parser.add_argument("--all", action="store_true", help="Render every editable folder under videos")
    parser.add_argument("--font-size", type=int, default=None, help="Set the English subtitle font size in pixels")
    args = parser.parse_args()

    if bool(args.video_folder) == args.all:
        raise SystemExit("Provide exactly one video_folder or --all.")

    if args.all:
        folders = sorted(path for path in VIDEOS_ROOT.iterdir() if path.is_dir())
        failures: list[str] = []
        rendered = 0
        for folder in folders:
            try:
                render_folder(folder, args.font_size)
                rendered += 1
            except (ValueError, subprocess.CalledProcessError) as error:
                failures.append(str(error))

        print(f"Rendered {rendered} folder(s).")
        if failures:
            raise SystemExit("Cannot render:\n  " + "\n  ".join(failures))
        return

    try:
        render_folder(args.video_folder, args.font_size)
    except (ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Cannot render: {error}") from error


if __name__ == "__main__":
    main()