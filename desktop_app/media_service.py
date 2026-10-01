"""Validated SRT-to-MP4 rendering for Subtitle Studio."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


TIMESTAMP = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2},\d{3})(?:\s+.*)?$"
)


class MediaError(RuntimeError):
    """An actionable media validation or rendering error."""


@dataclass(frozen=True)
class Cue:
    line_number: int
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True)
class RenderStyle:
    font_name: str = "Arial"
    font_size: int = 24
    placement: str = "bottom-center"
    offset_pixels: int = 24


def _timestamp_seconds(value: str) -> float:
    hours, minutes, seconds_milliseconds = value.split(":")
    seconds, milliseconds = seconds_milliseconds.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


def parse_srt(srt_path: Path) -> list[Cue]:
    cues: list[Cue] = []
    for line_number, line in enumerate(srt_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        match = TIMESTAMP.match(line.strip())
        if not match:
            continue
        start_seconds = _timestamp_seconds(match["start"])
        end_seconds = _timestamp_seconds(match["end"])
        if end_seconds <= start_seconds:
            raise MediaError(f"SRT line {line_number}: cue end must be after its start.")
        cues.append(Cue(line_number, start_seconds, end_seconds))
    if not cues:
        raise MediaError("No valid SRT timing cues found. Use UTF-8 SRT timestamps.")
    return cues


def _require_ffmpeg() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if not shutil.which(name)]
    if missing:
        raise MediaError(f"Bundled FFmpeg is unavailable: {', '.join(missing)}.")


def video_duration_seconds(video_path: Path) -> float:
    _require_ffmpeg()
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    duration = json.loads(result.stdout).get("format", {}).get("duration")
    if duration is None:
        raise MediaError("FFprobe could not read the MP4 duration.")
    return float(duration)


def validate_project(source_path: Path, srt_path: Path) -> tuple[list[Cue], float]:
    if not source_path.is_file():
        raise MediaError(f"Source MP4 not found: {source_path}")
    if not srt_path.is_file():
        raise MediaError(f"English SRT not found: {srt_path}")
    cues = parse_srt(srt_path)
    duration = video_duration_seconds(source_path)
    invalid = [cue for cue in cues if cue.end_seconds > duration]
    if invalid:
        cue = invalid[0]
        raise MediaError(
            f"SRT line {cue.line_number} ends at {cue.end_seconds:.3f}s, after the MP4 ends at {duration:.3f}s."
        )
    return cues, duration


def _ass_time(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    return f"{int(hours)}:{int(minutes):02}:{remainder:05.2f}"


def _ass_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")


def create_ass(srt_path: Path, ass_path: Path, style: RenderStyle) -> None:
    if style.font_size < 1:
        raise MediaError("Font size must be greater than zero.")
    if style.offset_pixels < 0:
        raise MediaError("Subtitle offset must be zero or greater.")
    alignment = {"top-center": 8, "bottom-center": 2, "below-hebrew": 2}.get(style.placement)
    if alignment is None:
        raise MediaError(f"Unknown subtitle placement: {style.placement}")

    lines = srt_path.read_text(encoding="utf-8-sig").splitlines()
    dialogues: list[str] = []
    index = 0
    while index < len(lines):
        if not TIMESTAMP.match(lines[index].strip()):
            index += 1
            continue
        match = TIMESTAMP.match(lines[index].strip())
        assert match is not None
        text_lines: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index])
            index += 1
        if text_lines:
            dialogues.append(
                f"Dialogue: 0,{_ass_time(_timestamp_seconds(match['start']))},{_ass_time(_timestamp_seconds(match['end']))},Default,,0,0,0,,{_ass_text(chr(10).join(text_lines))}"
            )

    margin_vertical = style.offset_pixels
    ass_path.write_text(
        "\n".join(
            [
                "[Script Info]",
                "ScriptType: v4.00+",
                "PlayResX: 1920",
                "PlayResY: 1080",
                "",
                "[V4+ Styles]",
                "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
                f"Style: Default,{style.font_name},{style.font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,{alignment},40,40,{margin_vertical},1",
                "",
                "[Events]",
                "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
                *dialogues,
            ]
        ),
        encoding="utf-8",
    )


def render(source_path: Path, srt_path: Path, output_path: Path, style: RenderStyle) -> tuple[int, float]:
    cues, duration = validate_project(source_path, srt_path)
    ass_path = output_path.with_suffix(".render.ass")
    try:
        create_ass(srt_path, ass_path, style)
        escaped_ass = ass_path.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(source_path), "-vf", f"ass=filename='{escaped_ass}'",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", "-movflags", "+faststart", str(output_path),
            ],
            check=True,
        )
    except subprocess.CalledProcessError as error:
        raise MediaError(f"FFmpeg could not render the MP4: {error}") from error
    finally:
        ass_path.unlink(missing_ok=True)
    return len(cues), duration