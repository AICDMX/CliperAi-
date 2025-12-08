"""Main application window for CLIPER GUI."""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from src.gui.utils.threading_helper import TaskRunner
from src.gui.utils.logger_bridge import LoggerBridge
from src.gui.utils.config_manager import GUIConfigManager, PipelineConfigManager
from src.gui.components.video_list import VideoList
from src.gui.components.log_viewer import LogViewer
from src.gui.components.status_bar import StatusBar
from src.gui.components.progress_dialog import ProgressDialog
from src.gui.widgets.download_widget import DownloadWidget
from src.gui.widgets.transcribe_widget import TranscribeWidget
from src.gui.widgets.clips_widget import ClipsWidget
from src.gui.widgets.captions_widget import CaptionsWidget
from src.gui.widgets.export_widget import ExportWidget


class MainWindow:
    """Main application window."""

    def __init__(self, logger_bridge: LoggerBridge):
        """
        Initialize main window.

        Args:
            logger_bridge: LoggerBridge instance for capturing logs

        """
        self.logger_bridge = logger_bridge
        self.config = GUIConfigManager()
        self.pipeline_config = PipelineConfigManager()

        self.root = tk.Tk()
        self.root.title("CLIPER - AI Video Clip Generator")
        self.root.geometry(self.config.get("window_geometry", "1200x800"))

        self.task_runner = TaskRunner(self.root)
        self.progress_dialog = None

        self.current_video_id = None

        self.setup_ui()
        self.setup_menu_bar()

        # Store reference to widgets for callbacks
        self.widgets = {}

    def setup_ui(self):
        """Setup main UI layout."""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left panel: Video list
        left_panel = tk.Frame(main_container)
        main_container.add(left_panel, weight=1)

        self.video_list = VideoList(left_panel, on_select_callback=self._on_video_select)
        self.video_list.pack(fill=tk.BOTH, expand=True)

        # Right panel: Tabs
        right_panel = tk.Frame(main_container)
        main_container.add(right_panel, weight=4)

        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add actual widget tabs
        self._setup_widget_tabs()

        # Bottom panel: Log viewer
        bottom_panel = tk.LabelFrame(
            self.root,
            text="",
            relief=tk.SUNKEN,
            bd=1,
        )
        bottom_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_viewer = LogViewer(bottom_panel, self.logger_bridge, height=6)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_bar = StatusBar(
            self.root, on_settings_click=self._on_settings_click
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_widget_tabs(self):
        """Setup tabs with actual pipeline widgets."""
        # Download
        download_frame = tk.Frame(self.notebook)
        self.notebook.add(download_frame, text="Download")
        self.download_widget = DownloadWidget(
            download_frame, self.task_runner, self
        )
        self.download_widget.pack(fill=tk.BOTH, expand=True)
        self.widgets["download"] = self.download_widget

        # Transcribe
        transcribe_frame = tk.Frame(self.notebook)
        self.notebook.add(transcribe_frame, text="Transcribe")
        self.transcribe_widget = TranscribeWidget(
            transcribe_frame, self.task_runner, self
        )
        self.transcribe_widget.pack(fill=tk.BOTH, expand=True)
        self.widgets["transcribe"] = self.transcribe_widget

        # Clips
        clips_frame = tk.Frame(self.notebook)
        self.notebook.add(clips_frame, text="Clips")
        self.clips_widget = ClipsWidget(clips_frame, self.task_runner, self)
        self.clips_widget.pack(fill=tk.BOTH, expand=True)
        self.widgets["clips"] = self.clips_widget

        # Captions
        captions_frame = tk.Frame(self.notebook)
        self.notebook.add(captions_frame, text="AI Captions")
        self.captions_widget = CaptionsWidget(
            captions_frame, self.task_runner, self
        )
        self.captions_widget.pack(fill=tk.BOTH, expand=True)
        self.widgets["captions"] = self.captions_widget

        # Export
        export_frame = tk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Export")
        self.export_widget = ExportWidget(export_frame, self.task_runner, self)
        self.export_widget.pack(fill=tk.BOTH, expand=True)
        self.widgets["export"] = self.export_widget

    def setup_menu_bar(self):
        """Setup menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self._on_close)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure API Keys", command=self._on_settings_click)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._on_about)

    def _on_video_select(self, video_id: str):
        """Handle video selection from list."""
        self.current_video_id = video_id
        self.status_bar.set_status(f"Selected: {video_id}")

        # Notify all widgets about the selected video
        for widget in self.widgets.values():
            if hasattr(widget, 'set_video'):
                widget.set_video(video_id)

    def _on_settings_click(self):
        """Handle settings button click."""
        messagebox.showinfo(
            "Settings",
            "Settings dialog not yet implemented.\n\n"
            "Edit your .env file to configure API keys.",
        )

    def _on_about(self):
        """Handle about menu click."""
        messagebox.showinfo(
            "About CLIPER",
            "CLIPER - AI-powered Video Clip Generator\n\n"
            "Transform long-form videos into publication-ready social media clips\n\n"
            "Version 1.0.0",
        )

    def _on_close(self):
        """Handle window close."""
        # Save window geometry
        self.config.set("window_geometry", self.root.geometry())

        # Cleanup
        self.task_runner.shutdown()
        self.logger_bridge.shutdown()

        self.root.destroy()

    def show_progress_dialog(self, title: str, message: str):
        """Show progress dialog."""
        if self.progress_dialog:
            self.progress_dialog.close()
        self.progress_dialog = ProgressDialog(self.root, title, message)

    def hide_progress_dialog(self):
        """Hide progress dialog."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def refresh_video_list(self):
        """Refresh video list display."""
        self.video_list.refresh()

    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
