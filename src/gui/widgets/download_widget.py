"""Download widget for the Download tab."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from src.downloader import YoutubeDownloader
from src.utils.state_manager import StateManager
from src.gui.utils.validators import Validators


class DownloadWidget(tk.Frame):
    """Widget for downloading YouTube videos."""

    def __init__(self, parent, task_runner, main_window):
        """
        Initialize download widget.

        Args:
            parent: Parent widget
            task_runner: TaskRunner for background operations
            main_window: Reference to main window for updates

        """
        super().__init__(parent)
        self.task_runner = task_runner
        self.main_window = main_window
        self.state_manager = StateManager()
        self.current_video_id = None
        self.setup_ui()

    def setup_ui(self):
        """Setup download widget UI."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main_frame,
            text="Download Video from YouTube",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # URL input
        ttk.Label(main_frame, text="YouTube URL:").grid(row=1, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Content type dropdown
        ttk.Label(main_frame, text="Content Type:").grid(row=2, column=0, sticky="w", pady=5)
        self.content_type_var = tk.StringVar(value="tutorial")
        content_types = ["tutorial", "livestream", "interview", "podcast", "conference"]
        content_combo = ttk.Combobox(
            main_frame,
            textvariable=self.content_type_var,
            values=content_types,
            state="readonly",
            width=47,
        )
        content_combo.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Quality dropdown
        ttk.Label(main_frame, text="Quality:").grid(row=3, column=0, sticky="w", pady=5)
        self.quality_var = tk.StringVar(value="best")
        qualities = ["best", "1080p", "720p", "480p", "360p"]
        quality_combo = ttk.Combobox(
            main_frame,
            textvariable=self.quality_var,
            values=qualities,
            state="readonly",
            width=47,
        )
        quality_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Download button
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="w", pady=20)

        download_btn = ttk.Button(
            button_frame,
            text="Download",
            command=self._on_download_click,
            width=20,
        )
        download_btn.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready to download",
            font=("TkDefaultFont", 9),
            fg="blue",
        )
        self.status_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)

    def set_video(self, video_id: str):
        """Set current video ID."""
        self.current_video_id = video_id

    def _on_download_click(self):
        """Handle download button click."""
        url = self.url_entry.get().strip()

        # Validate URL
        try:
            Validators.validate_youtube_url(url)
        except ValueError as e:
            messagebox.showwarning("Invalid Input", str(e))
            return

        self.status_label.config(text="Downloading...", fg="blue")
        self.main_window.show_progress_dialog("Downloading", f"Downloading video from YouTube...")

        def task():
            downloader = YoutubeDownloader()
            quality = self.quality_var.get()
            result = downloader.download(url, quality=quality)
            return result

        def callback(status, result):
            self.main_window.hide_progress_dialog()

            if status == "success" and result:
                # Register in state manager
                video_path = Path(result)
                video_id = video_path.stem.split("_")[-1]

                self.state_manager.register_video(
                    video_id=video_id,
                    filename=video_path.name,
                    content_type=self.content_type_var.get(),
                )

                self.status_label.config(
                    text=f"✓ Downloaded: {video_path.name}", fg="green"
                )
                self.url_entry.delete(0, tk.END)

                # Refresh video list
                self.main_window.refresh_video_list()
            else:
                error_msg = str(result) if result else "Unknown error"
                messagebox.showerror("Download Failed", f"Failed to download video:\n\n{error_msg}")
                self.status_label.config(text="Download failed", fg="red")

        self.task_runner.run_task(task, callback)
