"""Progress dialog component for showing operation progress."""

import tkinter as tk
from tkinter import ttk


class ProgressDialog:
    """Modal dialog showing progress of long-running operation."""

    def __init__(self, parent, title: str, message: str):
        """
        Initialize progress dialog.

        Args:
            parent: Parent window
            title: Dialog window title
            message: Initial status message

        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x120")
        self.dialog.resizable(False, False)

        # Make modal - disable parent window
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 60
        self.dialog.geometry(f"+{x}+{y}")

        self.setup_ui(message)

    def setup_ui(self, message: str):
        """Setup dialog UI components."""
        # Message label
        self.message_label = tk.Label(
            self.dialog,
            text=message,
            font=("TkDefaultFont", 10),
            wraplength=350,
        )
        self.message_label.pack(pady=15, padx=20)

        # Indeterminate progress bar
        self.progress = ttk.Progressbar(
            self.dialog,
            mode="indeterminate",
            length=350,
        )
        self.progress.pack(pady=10, padx=20)
        self.progress.start()

        # Prevent closing via window close button
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.bell)

    def update_message(self, new_message: str):
        """Update the status message."""
        self.message_label.config(text=new_message)
        self.dialog.update_idletasks()

    def close(self):
        """Close the progress dialog."""
        try:
            self.progress.stop()
            self.dialog.destroy()
        except tk.TclError:
            # Dialog already destroyed
            pass
