"""Offline Hebrew transcription using the bundled Ivrit CTranslate2 model."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


class TranscriptionError(RuntimeError):
    """An actionable offline transcription error."""


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str


def bundled_model_path() -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    model_path = root / "models" / "ivrit-whisper"
    required = ("config.json", "model.bin", "tokenizer.json")
    missing = [name for name in required if not (model_path / name).is_file()]
    if missing:
        raise TranscriptionError(
            f"The bundled Ivrit model is incomplete. Missing: {', '.join(missing)}. "
            "Copy the complete SubtitleStudio folder."
        )
    return model_path


def _srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{milliseconds:03}"


def _as_srt(segments: list[TranscriptSegment]) -> str:
    return "\n\n".join(
        f"{index}\n{_srt_timestamp(segment.start)} --> {_srt_timestamp(segment.end)}\n{segment.text}"
        for index, segment in enumerate(segments, start=1)
    ) + "\n"


def transcribe_hebrew(source_path: Path, project_folder: Path) -> tuple[int, float]:
    if not source_path.is_file():
        raise TranscriptionError(f"Source MP4 not found: {source_path}")
    model_path = bundled_model_path()
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(str(model_path), device="cpu", compute_type="int8")
        started = time.monotonic()
        raw_segments, info = model.transcribe(
            str(source_path),
            language="he",
            beam_size=5,
            vad_filter=True,
        )
        segments = [
            TranscriptSegment(start=raw.start, end=raw.end, text=raw.text.strip())
            for raw in raw_segments
            if raw.text.strip()
        ]
    except Exception as error:
        raise TranscriptionError(f"Hebrew transcription failed: {error}") from error

    if not segments:
        raise TranscriptionError("Ivrit found no Hebrew speech in this video.")
    payload = {
        "language": info.language,
        "duration": round(float(info.duration or 0), 3),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "segments": [asdict(segment) for segment in segments],
    }
    (project_folder / "transcript.he.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (project_folder / "subtitles.he.srt").write_text(_as_srt(segments), encoding="utf-8")
    return len(segments), payload["elapsed_seconds"]