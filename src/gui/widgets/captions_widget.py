"""Captions widget for the AI Captions tab."""

import tkinter as tk
from tkinter import ttk, messagebox

from src.copys_generator import CopysGenerator
from src.utils.state_manager import StateManager
from src.gui.utils.config_manager import PipelineConfigManager


class CaptionsWidget(tk.Frame):
    """Widget for generating AI captions."""

    def __init__(self, parent, task_runner, main_window):
        """Initialize captions widget."""
        super().__init__(parent)
        self.task_runner = task_runner
        self.main_window = main_window
        self.state_manager = StateManager()
        self.config = PipelineConfigManager()
        self.current_video_id = None
        self.setup_ui()

    def setup_ui(self):
        """Setup captions widget UI."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main_frame,
            text="Generate AI Captions",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Model dropdown
        ttk.Label(main_frame, text="Gemini Model:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.model_var = tk.StringVar(value="gemini-2.0-flash-exp")
        models = ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
        model_combo = ttk.Combobox(
            main_frame,
            textvariable=self.model_var,
            values=models,
            state="readonly",
            width=47,
        )
        model_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Auto-detect style checkbox
        self.auto_style_var = tk.BooleanVar(value=True)
        auto_check = ttk.Checkbutton(
            main_frame,
            text="Auto-detect clip style (viral/educational/storytelling)",
            variable=self.auto_style_var,
        )
        auto_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)

        # Generate button
        gen_btn = ttk.Button(
            main_frame,
            text="Generate Captions",
            command=self._on_generate_click,
            width=20,
        )
        gen_btn.grid(row=3, column=0, columnspan=2, sticky="w", pady=20)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Select a video with clips first",
            font=("TkDefaultFont", 9),
            fg="blue",
        )
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # Results treeview
        ttk.Label(main_frame, text="Generated Captions:").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(20, 5)
        )

        tree_frame = tk.Frame(main_frame)
        tree_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.captions_tree = ttk.Treeview(
            tree_frame,
            columns=("style", "score", "caption"),
            height=8,
            yscrollcommand=scrollbar.set,
        )
        self.captions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.captions_tree.yview)

        self.captions_tree.heading("#0", text="Clip #")
        self.captions_tree.heading("style", text="Style")
        self.captions_tree.heading("score", text="Score")
        self.captions_tree.heading("caption", text="Caption Preview")

        self.captions_tree.column("#0", width=50)
        self.captions_tree.column("style", width=80)
        self.captions_tree.column("score", width=60)
        self.captions_tree.column("caption", width=250)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def set_video(self, video_id: str):
        """Set current video."""
        self.current_video_id = video_id
        self.captions_tree.delete(*self.captions_tree.get_children())

        video_state = self.state_manager.get_video_state(video_id)
        if video_state:
            if not video_state.get("clips_generated"):
                self.status_label.config(
                    text="Clips must be generated first", fg="red"
                )
            else:
                self.status_label.config(text="Ready to generate captions", fg="blue")

    def _on_generate_click(self):
        """Handle generate button click."""
        if not self.current_video_id:
            messagebox.showwarning("No Video", "Please select a video first")
            return

        video_state = self.state_manager.get_video_state(self.current_video_id)
        if not video_state or not video_state.get("clips_generated"):
            messagebox.showwarning("No Clips", "Clips must be generated first")
            return

        # Validate API key
        try:
            self.config.validate_api_key()
        except ValueError as e:
            messagebox.showerror("API Key Missing", str(e))
            return

        self.status_label.config(text="Generating captions...", fg="blue")
        self.main_window.show_progress_dialog(
            "Generating Captions",
            "Using Gemini AI to generate engaging captions...",
        )

        def task():
            try:
                copys_gen = CopysGenerator(
                    self.current_video_id,
                    model_name=self.model_var.get(),
                )
                captions = copys_gen.generate_copys()
                return captions
            except Exception as e:
                raise e

        def callback(status, result):
            self.main_window.hide_progress_dialog()

            if status == "success":
                self.captions_tree.delete(*self.captions_tree.get_children())
                for i, caption in enumerate(result, 1):
                    style = caption.get("category", "unknown")
                    score = caption.get("engagement_score", 0)
                    text = caption.get("copy", "")[:70]

                    self.captions_tree.insert(
                        "",
                        tk.END,
                        text=f"#{i}",
                        values=(style, f"{score:.1f}", text),
                    )

                self.status_label.config(
                    text=f"✓ Generated {len(result)} captions", fg="green"
                )
            else:
                messagebox.showerror("Generation Failed", str(result))
                self.status_label.config(text="Generation failed", fg="red")

        self.task_runner.run_task(task, callback)
