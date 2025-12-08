"""Clips widget for the Clips tab."""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path

from src.clips_generator import ClipsGenerator
from src.utils.state_manager import StateManager


class ClipsWidget(tk.Frame):
    """Widget for generating clips."""

    def __init__(self, parent, task_runner, main_window):
        """Initialize clips widget."""
        super().__init__(parent)
        self.task_runner = task_runner
        self.main_window = main_window
        self.state_manager = StateManager()
        self.current_video_id = None
        self.clips_data = []
        self.setup_ui()

    def setup_ui(self):
        """Setup clips widget UI."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main_frame,
            text="Generate Clips",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")

        # Duration preset
        ttk.Label(main_frame, text="Duration Preset:").grid(row=1, column=0, sticky="w", pady=5)
        self.preset_var = tk.StringVar(value="medium")
        preset_options = ["short (30-60s)", "medium (30-90s)", "long (60-180s)", "custom"]
        preset_combo = ttk.Combobox(
            main_frame,
            textvariable=self.preset_var,
            values=preset_options,
            state="readonly",
            width=30,
        )
        preset_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=(10, 0))
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Custom duration fields (shown only when custom selected)
        ttk.Label(main_frame, text="Min Duration (s):").grid(row=2, column=0, sticky="w", pady=5)
        self.min_duration_var = tk.IntVar(value=30)
        min_spin = ttk.Spinbox(
            main_frame, from_=10, to=300, textvariable=self.min_duration_var, width=15
        )
        min_spin.grid(row=2, column=1, sticky="w", pady=5, padx=(10, 5))

        ttk.Label(main_frame, text="Max Duration (s):").grid(row=2, column=2, sticky="w", pady=5)
        self.max_duration_var = tk.IntVar(value=120)
        max_spin = ttk.Spinbox(
            main_frame, from_=10, to=600, textvariable=self.max_duration_var, width=15
        )
        max_spin.grid(row=2, column=3, sticky="w", pady=5, padx=(10, 0))

        # Max clips
        ttk.Label(main_frame, text="Max Clips:").grid(row=3, column=0, sticky="w", pady=5)
        self.max_clips_var = tk.IntVar(value=20)
        clips_spin = ttk.Spinbox(
            main_frame, from_=1, to=100, textvariable=self.max_clips_var, width=15
        )
        clips_spin.grid(row=3, column=1, sticky="w", pady=5, padx=(10, 5))

        # Generate button
        gen_btn = ttk.Button(
            main_frame,
            text="Generate Clips",
            command=self._on_generate_click,
            width=20,
        )
        gen_btn.grid(row=4, column=0, columnspan=2, sticky="w", pady=20)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Select a transcribed video first",
            font=("TkDefaultFont", 9),
            fg="blue",
        )
        self.status_label.grid(row=5, column=0, columnspan=4, sticky="w", pady=(10, 0))

        # Results treeview
        ttk.Label(main_frame, text="Generated Clips:").grid(
            row=6, column=0, columnspan=4, sticky="w", pady=(20, 5)
        )

        tree_frame = tk.Frame(main_frame)
        tree_frame.grid(row=7, column=0, columnspan=4, sticky="nsew", pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.clips_tree = ttk.Treeview(
            tree_frame,
            columns=("start", "end", "duration", "text"),
            height=8,
            yscrollcommand=scrollbar.set,
        )
        self.clips_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.clips_tree.yview)

        self.clips_tree.heading("#0", text="Clip #")
        self.clips_tree.heading("start", text="Start")
        self.clips_tree.heading("end", text="End")
        self.clips_tree.heading("duration", text="Duration")
        self.clips_tree.heading("text", text="Text Preview")

        self.clips_tree.column("#0", width=50)
        self.clips_tree.column("start", width=50)
        self.clips_tree.column("end", width=50)
        self.clips_tree.column("duration", width=50)
        self.clips_tree.column("text", width=200)

        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(7, weight=1)

    def _on_preset_change(self, event=None):
        """Handle preset change."""
        preset = self.preset_var.get()
        presets = {
            "short (30-60s)": (30, 60),
            "medium (30-90s)": (30, 90),
            "long (60-180s)": (60, 180),
        }
        if preset in presets:
            min_d, max_d = presets[preset]
            self.min_duration_var.set(min_d)
            self.max_duration_var.set(max_d)

    def set_video(self, video_id: str):
        """Set current video."""
        self.current_video_id = video_id
        self.clips_tree.delete(*self.clips_tree.get_children())

        video_state = self.state_manager.get_video_state(video_id)
        if video_state:
            if not video_state.get("transcribed"):
                self.status_label.config(
                    text="Video must be transcribed first", fg="red"
                )
            elif video_state.get("clips_generated"):
                self.status_label.config(
                    text=f"✓ Clips already generated: {len(video_state.get('clips', []))} clips",
                    fg="green",
                )
                self._load_clips()
            else:
                self.status_label.config(text="Ready to generate clips", fg="blue")

    def _on_generate_click(self):
        """Handle generate button click."""
        if not self.current_video_id:
            messagebox.showwarning("No Video", "Please select a video first")
            return

        video_state = self.state_manager.get_video_state(self.current_video_id)
        if not video_state or not video_state.get("transcribed"):
            messagebox.showwarning("Not Transcribed", "Video must be transcribed first")
            return

        self.status_label.config(text="Generating clips...", fg="blue")
        self.main_window.show_progress_dialog("Generating Clips", "Analyzing transcript...")

        def task():
            try:
                transcript_path = video_state.get("transcription_path")
                if not transcript_path or not Path(transcript_path).exists():
                    raise FileNotFoundError("Transcript not found")

                clips_gen = ClipsGenerator(
                    self.current_video_id,
                    min_duration=self.min_duration_var.get(),
                    max_duration=self.max_duration_var.get(),
                    max_clips=self.max_clips_var.get(),
                )

                clips = clips_gen.generate_clips()
                return clips
            except Exception as e:
                raise e

        def callback(status, result):
            self.main_window.hide_progress_dialog()

            if status == "success":
                self.state_manager.mark_clips_generated(self.current_video_id, result)
                self._load_clips()
                self.status_label.config(
                    text=f"✓ Generated {len(result)} clips", fg="green"
                )
            else:
                messagebox.showerror("Generation Failed", str(result))
                self.status_label.config(text="Generation failed", fg="red")

        self.task_runner.run_task(task, callback)

    def _load_clips(self):
        """Load and display clips in tree."""
        video_state = self.state_manager.get_video_state(self.current_video_id)
        if not video_state:
            return

        self.clips_tree.delete(*self.clips_tree.get_children())
        clips = video_state.get("clips", [])

        for i, clip in enumerate(clips, 1):
            start = clip.get("start", 0)
            end = clip.get("end", 0)
            duration = end - start
            text = clip.get("text", "")[:50]  # Truncate for display

            self.clips_tree.insert(
                "",
                tk.END,
                text=f"#{i}",
                values=(f"{start:.1f}s", f"{end:.1f}s", f"{duration:.1f}s", text),
            )
