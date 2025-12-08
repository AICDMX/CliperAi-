"""Status bar component for showing current status."""

import tkinter as tk
from tkinter import ttk


class StatusBar(tk.Frame):
    """Status bar showing current status and settings button."""

    def __init__(self, parent, on_settings_click=None):
        """
        Initialize status bar.

        Args:
            parent: Parent widget
            on_settings_click: Callback when settings button is clicked

        """
        super().__init__(parent, relief=tk.SUNKEN, bd=1)
        self.on_settings_click = on_settings_click
        self.setup_ui()

    def setup_ui(self):
        """Setup status bar UI."""
        # Left side: status message
        self.status_label = tk.Label(
            self,
            text="Ready",
            font=("TkDefaultFont", 9),
            anchor="w",
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=3)

        # Right side: settings button
        settings_btn = ttk.Button(
            self,
            text="⚙️ Settings",
            width=12,
            command=self.on_settings_click or self._dummy_callback,
        )
        settings_btn.pack(side=tk.RIGHT, padx=5, pady=3)

    def set_status(self, message: str):
        """Update status message."""
        self.status_label.config(text=message)
        self.update_idletasks()

    def _dummy_callback(self):
        """Dummy callback if none provided."""
        pass
