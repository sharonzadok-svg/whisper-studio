"""Validate an SRT against an MP4, then burn it into a new MP4.

Example:
    python tools\burn_subtitles.py input.mp4 english.srt output.mp4

Requires FFmpeg and FFprobe on PATH. The tool rejects malformed timestamps and
cues outside the video duration before starting the expensive render.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


TIMESTAMP = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2},\d{3})(?:\s+.*)?$"
)


@dataclass(frozen=True)
class Cue:
    number: int
    start_seconds: float
    end_seconds: float


def parse_timestamp(value: str) -> float:
    hours, minutes, seconds_milliseconds = value.split(":")
    seconds, milliseconds = seconds_milliseconds.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


def parse_srt(srt_path: Path) -> list[Cue]:
    cues: list[Cue] = []
    for line_number, line in enumerate(srt_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        match = TIMESTAMP.match(line.strip())
        if not match:
            continue

        start_seconds = parse_timestamp(match["start"])
        end_seconds = parse_timestamp(match["end"])
        if end_seconds <= start_seconds:
            raise ValueError(f"Invalid cue at SRT line {line_number}: end time must be after start time.")
        cues.append(Cue(line_number, start_seconds, end_seconds))

    if not cues:
        raise ValueError("No valid SRT timing cues found. Use UTF-8 SRT timestamps such as 00:00:01,500 --> 00:00:03,000.")
    return cues


def get_video_duration(input_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(input_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    duration = json.loads(result.stdout).get("format", {}).get("duration")
    if duration is None:
        raise ValueError("FFprobe could not determine the MP4 duration.")
    return float(duration)


def validate_timing(cues: list[Cue], video_duration: float) -> None:
    errors: list[str] = []
    for cue in cues:
        if cue.start_seconds < 0:
            errors.append(f"SRT line {cue.number}: cue starts before 00:00:00,000.")
        if cue.end_seconds > video_duration:
            errors.append(
                f"SRT line {cue.number}: cue ends at {cue.end_seconds:.3f}s, after video duration {video_duration:.3f}s."
            )
    if errors:
        raise ValueError("\n".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_mp4", type=Path, help="Source MP4 with no subtitles")
    parser.add_argument("input_srt", type=Path, help="Timed English SRT for this exact source video")
    parser.add_argument("output_mp4", type=Path, help="New MP4 with burned subtitles")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output file")
    parser.add_argument("--font-size", type=int, default=None, help="Set the English subtitle font size in pixels")
    args = parser.parse_args()

    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise SystemExit(f"{executable} is required on PATH. Install FFmpeg, reopen the terminal, and retry.")
    if not args.input_mp4.is_file():
        raise SystemExit(f"Input MP4 not found: {args.input_mp4}")
    if not args.input_srt.is_file():
        raise SystemExit(f"Input SRT not found: {args.input_srt}")
    if args.output_mp4.exists() and not args.overwrite:
        raise SystemExit(f"Output already exists: {args.output_mp4}. Use --overwrite to replace it.")

    try:
        cues = parse_srt(args.input_srt)
        video_duration = get_video_duration(args.input_mp4)
        validate_timing(cues, video_duration)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Subtitle timing validation failed: {error}") from error

    print(
        f"Timing check passed: {len(cues)} cues, "
        f"first cue {cues[0].start_seconds:.3f}s, last cue {cues[-1].end_seconds:.3f}s, "
        f"video {video_duration:.3f}s."
    )
    args.output_mp4.parent.mkdir(parents=True, exist_ok=True)
    subtitle_path = args.input_srt.resolve().as_posix()
    subtitle_path = subtitle_path.replace(":", r"\:").replace("'", r"\'")
    if args.font_size is not None:
        if args.font_size < 1:
            raise SystemExit("--font-size must be greater than zero.")
    subtitle_filter = f"subtitles=filename='{subtitle_path}':charenc=UTF-8"
    if args.font_size is not None:
        subtitle_filter += f":force_style='FontSize={args.font_size}'"
    command = [
        "ffmpeg",
        "-y" if args.overwrite else "-n",
        "-i",
        str(args.input_mp4),
        "-vf",
        subtitle_filter,
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        str(args.output_mp4),
    ]
    print("Burning subtitles after the timing check passed.")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()