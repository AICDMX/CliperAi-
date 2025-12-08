"""Transcribe widget for the Transcribe tab."""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from src.transcriber import Transcriber
from src.utils.state_manager import StateManager
from src.gui.utils.validators import Validators


class TranscribeWidget(tk.Frame):
    """Widget for transcribing videos."""

    def __init__(self, parent, task_runner, main_window):
        """
        Initialize transcribe widget.

        Args:
            parent: Parent widget
            task_runner: TaskRunner for background operations
            main_window: Reference to main window

        """
        super().__init__(parent)
        self.task_runner = task_runner
        self.main_window = main_window
        self.state_manager = StateManager()
        self.current_video_id = None
        self.setup_ui()

    def setup_ui(self):
        """Setup transcribe widget UI."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main_frame,
            text="Transcribe Video",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Whisper model dropdown
        ttk.Label(main_frame, text="Whisper Model:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.model_var = tk.StringVar(value="base")
        model_options = ["tiny", "base", "small", "medium", "large-v2"]
        model_combo = ttk.Combobox(
            main_frame,
            textvariable=self.model_var,
            values=model_options,
            state="readonly",
            width=47,
        )
        model_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Language dropdown
        ttk.Label(main_frame, text="Language:").grid(row=2, column=0, sticky="w", pady=5)
        self.language_var = tk.StringVar(value="auto")
        languages = ["auto", "en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"]
        language_combo = ttk.Combobox(
            main_frame,
            textvariable=self.language_var,
            values=languages,
            state="readonly",
            width=47,
        )
        language_combo.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Transcribe button
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=20)

        transcribe_btn = ttk.Button(
            button_frame,
            text="Transcribe",
            command=self._on_transcribe_click,
            width=20,
        )
        transcribe_btn.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Select a video first",
            font=("TkDefaultFont", 9),
            fg="blue",
        )
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)

    def set_video(self, video_id: str):
        """Set current video and update status."""
        self.current_video_id = video_id

        video_state = self.state_manager.get_video_state(video_id)
        if video_state:
            if video_state.get("transcribed"):
                self.status_label.config(
                    text=f"✓ Already transcribed: {video_state['filename']}", fg="green"
                )
            else:
                self.status_label.config(
                    text=f"Ready to transcribe: {video_state['filename']}", fg="blue"
                )
        else:
            self.status_label.config(text="Video not found", fg="red")

    def _on_transcribe_click(self):
        """Handle transcribe button click."""
        if not self.current_video_id:
            messagebox.showwarning("No Video Selected", "Please select a video first")
            return

        video_state = self.state_manager.get_video_state(self.current_video_id)
        if not video_state:
            messagebox.showerror("Error", "Video not found in state")
            return

        if not video_state.get("downloaded"):
            messagebox.showwarning("Not Downloaded", "Video must be downloaded first")
            return

        self.status_label.config(text="Transcribing...", fg="blue")
        self.main_window.show_progress_dialog(
            "Transcribing",
            f"Transcribing: {video_state['filename']}\n\nThis may take several minutes...",
        )

        def task():
            try:
                video_path = Path("downloads") / video_state["filename"]
                if not video_path.exists():
                    raise FileNotFoundError(f"Video file not found: {video_path}")

                transcriber = Transcriber(model_size=self.model_var.get())

                # Create output paths
                output_dir = Path("temp")
                output_dir.mkdir(exist_ok=True)
                transcript_path = output_dir / f"{self.current_video_id}_transcript.json"

                # Transcribe
                result = transcriber.transcribe(
                    str(video_path),
                    language="None" if self.language_var.get() == "auto" else self.language_var.get(),
                    output_file=str(transcript_path),
                )

                return str(transcript_path)
            except Exception as e:
                raise e

        def callback(status, result):
            self.main_window.hide_progress_dialog()

            if status == "success":
                self.state_manager.mark_transcribed(
                    self.current_video_id, str(result)
                )
                self.status_label.config(
                    text="✓ Transcription complete", fg="green"
                )
            else:
                error_msg = str(result)
                messagebox.showerror("Transcription Failed", f"Error:\n\n{error_msg}")
                self.status_label.config(text="Transcription failed", fg="red")

        self.task_runner.run_task(task, callback)
