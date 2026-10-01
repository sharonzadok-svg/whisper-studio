"""Portable desktop editor for timed SRT subtitles and MP4 rendering."""

from __future__ import annotations

import os
import shutil
import sys
import threading
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, Y, filedialog, messagebox, ttk
import tkinter as tk

try:
    from .media_service import MediaError, RenderStyle, render, validate_project
    from .transcription_service import TranscriptionError, transcribe_hebrew
except ImportError:
    from media_service import MediaError, RenderStyle, render, validate_project
    from transcription_service import TranscriptionError, transcribe_hebrew


APP_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
WINDOW_TITLE = "Subtitle Studio"


class SubtitleStudio(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=14)
        self.root = root
        self.project_folder: Path | None = None
        self.font_name = tk.StringVar(value="Arial")
        self.font_size = tk.IntVar(value=24)
        self.placement = tk.StringVar(value="bottom-center")
        self.offset_pixels = tk.IntVar(value=24)
        self.status = tk.StringVar(value="Choose a video project folder to begin.")
        self._build()
        self._configure_ffmpeg_path()

    def _build(self) -> None:
        self.pack(fill=BOTH, expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(1, weight=1)
        ttk.Button(header, text="Open Project Folder", command=self.open_project).grid(row=0, column=0, sticky="w")
        self.project_label = ttk.Label(header, text="No project selected", anchor="w")
        self.project_label.grid(row=0, column=1, sticky="ew", padx=10)
        ttk.Button(header, text="Open Source", command=lambda: self.open_media("source.mp4")).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(header, text="Open Output", command=lambda: self.open_media("output.en.mp4")).grid(row=0, column=3)

        requirements = ttk.LabelFrame(self, text="Project files", padding=8)
        requirements.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(requirements, text="Change font or placement, then re-render from the existing English SRT. Hebrew transcription runs only when selected.").pack(anchor="w")

        style = ttk.LabelFrame(self, text="English subtitle style", padding=8)
        style.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        style.columnconfigure(7, weight=1)
        ttk.Label(style, text="Preset").grid(row=0, column=0, sticky="w")
        preset = ttk.Combobox(style, state="readonly", values=["Standard bottom", "Below Hebrew"], width=18)
        preset.current(0)
        preset.grid(row=0, column=1, sticky="w", padx=(4, 12))
        preset.bind("<<ComboboxSelected>>", lambda event: self.apply_preset(preset.get()))
        ttk.Label(style, text="Font").grid(row=0, column=2, sticky="w")
        ttk.Combobox(style, textvariable=self.font_name, values=["Arial", "Calibri", "Tahoma", "Verdana"], width=12).grid(row=0, column=3, sticky="w", padx=(4, 12))
        ttk.Label(style, text="Size").grid(row=0, column=4, sticky="w")
        ttk.Spinbox(style, from_=6, to=96, textvariable=self.font_size, width=5).grid(row=0, column=5, sticky="w", padx=(4, 12))
        ttk.Label(style, text="Offset px").grid(row=0, column=6, sticky="w")
        ttk.Spinbox(style, from_=0, to=400, textvariable=self.offset_pixels, width=5).grid(row=0, column=7, sticky="w", padx=4)

        editor = ttk.LabelFrame(self, text="Editable English SRT", padding=8)
        editor.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        editor.columnconfigure(0, weight=1)
        editor.rowconfigure(0, weight=1)
        self.srt_text = tk.Text(editor, wrap="word", undo=True, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(editor, orient="vertical", command=self.srt_text.yview)
        self.srt_text.configure(yscrollcommand=scrollbar.set)
        self.srt_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        actions = ttk.Frame(self)
        actions.grid(row=4, column=0, sticky="ew")
        self.transcribe_button = ttk.Button(actions, text="Create Hebrew Transcript", command=self.start_transcription)
        self.transcribe_button.pack(side=LEFT)
        ttk.Button(actions, text="Save SRT", command=self.save_srt).pack(side=LEFT)
        ttk.Button(actions, text="Validate Timing", command=self.validate).pack(side=LEFT, padx=8)
        self.render_button = ttk.Button(actions, text="Apply Font & Re-render MP4", command=self.start_render)
        self.render_button.pack(side=LEFT)
        ttk.Label(actions, textvariable=self.status, anchor="e").pack(side=RIGHT, fill=X, expand=True)

    def _configure_ffmpeg_path(self) -> None:
        candidates = [APP_ROOT / "ffmpeg" / "bin", APP_ROOT / "ffmpeg"]
        for candidate in candidates:
            if (candidate / "ffmpeg.exe").is_file() and (candidate / "ffprobe.exe").is_file():
                os.environ["PATH"] = f"{candidate}{os.pathsep}{os.environ.get('PATH', '')}"
                return
        if not shutil.which("ffmpeg"):
            self.status.set("FFmpeg is not bundled yet. Rendering is unavailable.")

    def apply_preset(self, preset: str) -> None:
        if preset == "Below Hebrew":
            self.placement.set("below-hebrew")
            self.font_size.set(10)
            self.offset_pixels.set(10)
        else:
            self.placement.set("bottom-center")
            self.font_size.set(24)
            self.offset_pixels.set(24)

    def open_project(self) -> None:
        selected = filedialog.askdirectory(title="Choose a video project folder")
        if not selected:
            return
        folder = Path(selected)
        source = folder / "source.mp4"
        srt = folder / "subtitles.en.srt"
        if not source.is_file():
            messagebox.showerror(WINDOW_TITLE, "The folder must contain source.mp4.")
            return
        self.project_folder = folder
        self.project_label.configure(text=str(folder))
        self.srt_text.delete("1.0", END)
        if srt.is_file():
            self.srt_text.insert("1.0", srt.read_text(encoding="utf-8-sig"))
            self.status.set("Project loaded. Edit subtitles, then validate or render.")
        else:
            self.status.set("Project loaded. Create a Hebrew transcript or add an English SRT.")

    def _paths(self) -> tuple[Path, Path, Path]:
        if self.project_folder is None:
            raise MediaError("Choose a project folder first.")
        return (
            self.project_folder / "source.mp4",
            self.project_folder / "subtitles.en.srt",
            self.project_folder / "output.en.mp4",
        )

    def save_srt(self) -> bool:
        try:
            _, srt, _ = self._paths()
            content = self.srt_text.get("1.0", END).rstrip() + "\n"
            if not content.strip():
                raise MediaError("English SRT cannot be empty.")
            srt.write_text(content, encoding="utf-8")
            self.status.set("English SRT saved.")
            return True
        except (OSError, MediaError) as error:
            messagebox.showerror(WINDOW_TITLE, str(error))
            return False

    def validate(self) -> None:
        if not self.save_srt():
            return
        try:
            source, srt, _ = self._paths()
            cues, duration = validate_project(source, srt)
            self.status.set(f"Timing valid: {len(cues)} cues within {duration:.2f} seconds.")
        except MediaError as error:
            messagebox.showerror(WINDOW_TITLE, str(error))

    def start_render(self) -> None:
        if not self.save_srt():
            return
        self.render_button.configure(state="disabled")
        self.status.set("Applying style to the existing English SRT and rendering MP4. This can take a few minutes.")
        threading.Thread(target=self._render_worker, daemon=True).start()

    def start_transcription(self) -> None:
        try:
            self._paths()
        except MediaError as error:
            messagebox.showerror(WINDOW_TITLE, str(error))
            return
        self.transcribe_button.configure(state="disabled")
        self.status.set("Creating Hebrew transcript. This can take several minutes on CPU.")
        threading.Thread(target=self._transcription_worker, daemon=True).start()

    def _transcription_worker(self) -> None:
        try:
            source, _, _ = self._paths()
            assert self.project_folder is not None
            segments, elapsed = transcribe_hebrew(source, self.project_folder)
            self.root.after(0, lambda: self._transcription_finished(segments, elapsed))
        except (TranscriptionError, MediaError, OSError) as error:
            self.root.after(0, lambda: self._transcription_failed(str(error)))

    def _transcription_finished(self, segments: int, elapsed: float) -> None:
        self.transcribe_button.configure(state="normal")
        message = f"Created subtitles.he.srt with {segments} Hebrew cues in {elapsed:.1f} seconds."
        self.status.set(message)
        messagebox.showinfo(WINDOW_TITLE, message)

    def _transcription_failed(self, message: str) -> None:
        self.transcribe_button.configure(state="normal")
        self.status.set("Hebrew transcription failed.")
        messagebox.showerror(WINDOW_TITLE, message)

    def _render_worker(self) -> None:
        try:
            source, srt, output = self._paths()
            style = RenderStyle(
                font_name=self.font_name.get().strip(),
                font_size=self.font_size.get(),
                placement=self.placement.get(),
                offset_pixels=self.offset_pixels.get(),
            )
            cues, duration = render(source, srt, output, style)
            self.root.after(0, lambda: self._render_finished(f"Rendered {cues} cues into output.en.mp4 ({duration:.2f}s)."))
        except (MediaError, OSError, tk.TclError) as error:
            self.root.after(0, lambda: self._render_failed(str(error)))

    def _render_finished(self, message: str) -> None:
        self.render_button.configure(state="normal")
        self.status.set(message)
        messagebox.showinfo(WINDOW_TITLE, message)

    def _render_failed(self, message: str) -> None:
        self.render_button.configure(state="normal")
        self.status.set("Render failed.")
        messagebox.showerror(WINDOW_TITLE, message)

    def open_media(self, filename: str) -> None:
        try:
            source, _, output = self._paths()
            target = source if filename == "source.mp4" else output
            if not target.is_file():
                raise MediaError(f"File not found: {target.name}")
            os.startfile(target)  # type: ignore[attr-defined]
        except MediaError as error:
            messagebox.showerror(WINDOW_TITLE, str(error))


def main() -> None:
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("1000x760")
    root.minsize(760, 560)
    SubtitleStudio(root)
    root.mainloop()


if __name__ == "__main__":
    main()