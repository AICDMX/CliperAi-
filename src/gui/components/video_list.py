"""Video list component for displaying all videos with status."""

import tkinter as tk
from tkinter import ttk
from src.utils.state_manager import StateManager


class VideoList(tk.Frame):
    """Treeview showing all videos with status badges."""

    def __init__(self, parent, on_select_callback=None):
        """
        Initialize video list.

        Args:
            parent: Parent widget
            on_select_callback: Called when video is selected with video_id

        """
        super().__init__(parent)
        self.on_select = on_select_callback
        self.state_manager = StateManager()
        self.setup_ui()
        self.load_videos()

    def setup_ui(self):
        """Setup video list UI."""
        # Header
        header = tk.Label(
            self,
            text="Videos",
            font=("TkDefaultFont", 9, "bold"),
            anchor="w",
        )
        header.pack(fill=tk.X, padx=5, pady=2)

        # Treeview with scrollbar
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("status",),
            height=15,
            yscrollcommand=scrollbar.set,
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        # Configure columns
        self.tree.heading("#0", text="Video")
        self.tree.column("#0", width=120)
        self.tree.heading("status", text="Status")
        self.tree.column("status", width=50)

        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Right-click context menu
        self.tree.bind("<Button-3>", self._on_right_click)
        self._setup_context_menu()

    def _setup_context_menu(self):
        """Setup right-click context menu."""
        self.context_menu = tk.Menu(self, tearoff=False)
        self.context_menu.add_command(
            label="Delete Video", command=self._delete_selected
        )

    def load_videos(self):
        """Load all videos from state manager."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Load from state
        all_videos = self.state_manager.get_all_videos()

        for video_id, video_state in all_videos.items():
            status_str = self._get_status_str(video_state)
            self.tree.insert("", tk.END, video_id, text=video_id, values=(status_str,))

    def _get_status_str(self, video_state: dict) -> str:
        """Get status badge string for video."""
        badges = []

        # Download status
        if video_state.get("downloaded"):
            badges.append("✓")
        else:
            badges.append("○")

        # Transcribed status
        if video_state.get("transcribed"):
            badges.append("✓")
        else:
            badges.append("○")

        # Clips generated status
        if video_state.get("clips_generated"):
            badges.append("✓")
        else:
            badges.append("○")

        # Export status
        if video_state.get("clips_exported"):
            badges.append("✓")
        else:
            badges.append("○")

        return "".join(badges)

    def _on_select(self, event):
        """Handle video selection."""
        selection = self.tree.selection()
        if selection and self.on_select:
            video_id = selection[0]
            self.on_select(video_id)

    def _on_right_click(self, event):
        """Handle right-click context menu."""
        try:
            item = self.tree.selection_get()[0]
            self.context_menu.post(event.x_root, event.y_root)
        except IndexError:
            pass

    def _delete_selected(self):
        """Delete selected video from state."""
        selection = self.tree.selection()
        if selection:
            video_id = selection[0]
            self.state_manager.clear_video_state(video_id)
            self.load_videos()

    def refresh(self):
        """Refresh video list from state."""
        self.load_videos()

    def get_selected_video(self) -> str:
        """Get currently selected video ID."""
        selection = self.tree.selection()
        return selection[0] if selection else None
