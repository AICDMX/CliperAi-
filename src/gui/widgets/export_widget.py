"""Export widget for the Export tab."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from src.video_exporter import VideoExporter
from src.utils.state_manager import StateManager
from src.gui.utils.validators import Validators
from src.gui.utils.config_manager import GUIConfigManager


class ExportWidget(tk.Frame):
    """Widget for exporting video clips."""

    def __init__(self, parent, task_runner, main_window):
        """Initialize export widget."""
        super().__init__(parent)
        self.task_runner = task_runner
        self.main_window = main_window
        self.state_manager = StateManager()
        self.gui_config = GUIConfigManager()
        self.current_video_id = None
        self.logo_path = None
        self.setup_ui()

    def setup_ui(self):
        """Setup export widget UI."""
        # Create scrollable frame
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main_frame = ttk.Frame(scrollable_frame, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main_frame,
            text="Export Video Clips",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")

        # Aspect ratio
        ttk.Label(main_frame, text="Aspect Ratio:").grid(row=1, column=0, sticky="w", pady=10)
        aspect_frame = tk.Frame(main_frame)
        aspect_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=(10, 0))

        self.aspect_var = tk.StringVar(
            value=self.gui_config.get("default_aspect_ratio", "original")
        )
        for aspect in ["original", "9:16", "1:1"]:
            ttk.Radiobutton(
                aspect_frame,
                text=aspect,
                variable=self.aspect_var,
                value=aspect,
            ).pack(side=tk.LEFT, padx=5)

        # Subtitles
        ttk.Label(main_frame, text="Subtitles:").grid(row=2, column=0, sticky="w", pady=10)
        self.subtitles_var = tk.BooleanVar(
            value=self.gui_config.get("enable_subtitles", True)
        )
        ttk.Checkbutton(
            main_frame,
            text="Add subtitles to clips",
            variable=self.subtitles_var,
        ).grid(row=2, column=1, sticky="w", padx=(10, 0))

        # Face tracking
        self.face_tracking_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame,
            text="Enable face tracking (for vertical videos)",
            variable=self.face_tracking_var,
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=0, pady=10)

        # Logo overlay
        ttk.Label(main_frame, text="Logo Overlay:").grid(row=4, column=0, sticky="w", pady=10)
        self.logo_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame,
            text="Enable logo overlay",
            variable=self.logo_enabled_var,
            command=self._toggle_logo_options,
        ).grid(row=4, column=1, columnspan=2, sticky="w", padx=(10, 0))

        # Logo file picker
        ttk.Label(main_frame, text="Logo File:").grid(row=5, column=0, sticky="w", pady=10)
        logo_button_frame = tk.Frame(main_frame)
        logo_button_frame.grid(row=5, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        self.logo_label = tk.Label(logo_button_frame, text="No logo selected", fg="gray")
        self.logo_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        logo_browse_btn = ttk.Button(
            logo_button_frame,
            text="Browse...",
            command=self._browse_logo,
            width=10,
        )
        logo_browse_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Logo position
        ttk.Label(main_frame, text="Logo Position:").grid(row=6, column=0, sticky="w", pady=10)
        self.logo_pos_var = tk.StringVar(value="bottom-right")
        pos_options = ["top-left", "top-right", "bottom-left", "bottom-right"]
        pos_combo = ttk.Combobox(
            main_frame,
            textvariable=self.logo_pos_var,
            values=pos_options,
            state="readonly",
            width=30,
        )
        pos_combo.grid(row=6, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        # Logo scale
        ttk.Label(main_frame, text="Logo Scale:").grid(row=7, column=0, sticky="w", pady=10)
        self.logo_scale_var = tk.DoubleVar(value=0.15)
        scale_slider = ttk.Scale(
            main_frame,
            from_=0.05,
            to=0.3,
            variable=self.logo_scale_var,
            orient=tk.HORIZONTAL,
        )
        scale_slider.grid(row=7, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        # Output directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=8, column=0, sticky="w", pady=10)
        output_frame = tk.Frame(main_frame)
        output_frame.grid(row=8, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        self.output_label = tk.Label(
            output_frame,
            text=self.gui_config.get("last_output_dir", str(Path.home() / "Downloads")),
            fg="blue",
        )
        self.output_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        output_browse_btn = ttk.Button(
            output_frame,
            text="Browse...",
            command=self._browse_output_dir,
            width=10,
        )
        output_browse_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Organize by category
        self.organize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main_frame,
            text="Organize by clip category (viral/educational/storytelling)",
            variable=self.organize_var,
        ).grid(row=9, column=0, columnspan=3, sticky="w", pady=10)

        # Export button
        export_btn = ttk.Button(
            main_frame,
            text="Export All Clips",
            command=self._on_export_click,
            width=20,
        )
        export_btn.grid(row=10, column=0, columnspan=3, sticky="w", pady=20)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Select a video with clips first",
            font=("TkDefaultFont", 9),
            fg="blue",
        )
        self.status_label.grid(row=11, column=0, columnspan=3, sticky="w")

        main_frame.columnconfigure(1, weight=1)

        # Initially disable logo options
        self._toggle_logo_options()

    def _toggle_logo_options(self):
        """Toggle logo option visibility."""
        state = "normal" if self.logo_enabled_var.get() else "disabled"
        # This is simplified - in real app, would disable specific widgets

    def _browse_logo(self):
        """Browse for logo file."""
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            try:
                Validators.validate_logo_path(path)
                self.logo_path = path
                self.logo_label.config(text=Path(path).name, fg="black")
            except ValueError as e:
                messagebox.showerror("Invalid File", str(e))

    def _browse_output_dir(self):
        """Browse for output directory."""
        path = filedialog.askdirectory()
        if path:
            try:
                Validators.validate_output_directory(path)
                self.output_label.config(text=path)
                self.gui_config.set("last_output_dir", path)
            except ValueError as e:
                messagebox.showerror("Invalid Directory", str(e))

    def set_video(self, video_id: str):
        """Set current video."""
        self.current_video_id = video_id

        video_state = self.state_manager.get_video_state(video_id)
        if video_state:
            if not video_state.get("clips_generated"):
                self.status_label.config(
                    text="Clips must be generated first", fg="red"
                )
            else:
                self.status_label.config(
                    text=f"Ready to export {len(video_state.get('clips', []))} clips",
                    fg="blue",
                )

    def _on_export_click(self):
        """Handle export button click."""
        if not self.current_video_id:
            messagebox.showwarning("No Video", "Please select a video first")
            return

        video_state = self.state_manager.get_video_state(self.current_video_id)
        if not video_state or not video_state.get("clips_generated"):
            messagebox.showwarning("No Clips", "Clips must be generated first")
            return

        # Validate output directory
        try:
            output_dir = self.output_label.cget("text")
            Validators.validate_output_directory(output_dir)
        except ValueError as e:
            messagebox.showerror("Invalid Output", str(e))
            return

        # Validate logo if enabled
        if self.logo_enabled_var.get():
            try:
                Validators.validate_logo_path(self.logo_path or "")
            except ValueError as e:
                messagebox.showerror("Invalid Logo", str(e))
                return

        self.status_label.config(text="Exporting clips...", fg="blue")
        self.main_window.show_progress_dialog("Exporting", "Exporting video clips...")

        def task():
            try:
                video_path = Path("downloads") / video_state["filename"]

                exporter = VideoExporter(
                    video_id=self.current_video_id,
                    video_path=str(video_path),
                    output_dir=self.output_label.cget("text"),
                    aspect_ratio=self.aspect_var.get(),
                    add_subtitles=self.subtitles_var.get(),
                    face_tracking=self.face_tracking_var.get(),
                    logo_path=self.logo_path,
                    logo_position=self.logo_pos_var.get(),
                    logo_scale=self.logo_scale_var.get(),
                    organize_by_category=self.organize_var.get(),
                )

                exported = exporter.export_all()
                return exported
            except Exception as e:
                raise e

        def callback(status, result):
            self.main_window.hide_progress_dialog()

            if status == "success":
                self.state_manager.mark_clips_exported(
                    self.current_video_id,
                    result,
                    aspect_ratio=self.aspect_var.get(),
                )
                messagebox.showinfo(
                    "Export Success",
                    f"Successfully exported {len(result)} clips!\n\n"
                    f"Output: {self.output_label.cget('text')}",
                )
                self.status_label.config(text="✓ Export complete", fg="green")
            else:
                messagebox.showerror("Export Failed", str(result))
                self.status_label.config(text="Export failed", fg="red")

        self.task_runner.run_task(task, callback)
