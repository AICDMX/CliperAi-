"""Log viewer component for displaying application logs."""

import tkinter as tk
from tkinter import ttk


class LogViewer(tk.Frame):
    """Scrolled text widget for displaying logs with color coding."""

    def __init__(self, parent, logger_bridge, height=100):
        """
        Initialize log viewer.

        Args:
            parent: Parent widget
            logger_bridge: LoggerBridge instance for getting logs
            height: Height in characters

        """
        super().__init__(parent)
        self.logger_bridge = logger_bridge
        self.height = height
        self.setup_ui()
        self.start_polling()

    def setup_ui(self):
        """Setup log viewer UI."""
        # Header
        header = tk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(header, text="Log Output", font=("TkDefaultFont", 9, "bold")).pack(
            side=tk.LEFT
        )

        clear_btn = ttk.Button(
            header,
            text="Clear",
            width=8,
            command=self.clear,
        )
        clear_btn.pack(side=tk.RIGHT)

        # Text widget with scrollbar
        text_frame = tk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(
            text_frame,
            height=self.height,
            width=80,
            yscrollcommand=scrollbar.set,
            font=("Courier", 8),
            state=tk.DISABLED,
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text.yview)

        # Configure color tags for log levels
        self.text.tag_config("INFO", foreground="black")
        self.text.tag_config("SUCCESS", foreground="green")
        self.text.tag_config("WARNING", foreground="orange")
        self.text.tag_config("ERROR", foreground="red")
        self.text.tag_config("DEBUG", foreground="gray")

    def poll_logs(self):
        """Poll logger bridge for new logs and update display."""
        new_logs = self.logger_bridge.get_logs()

        if new_logs:
            self.text.config(state=tk.NORMAL)

            for log_line in new_logs:
                # Parse log level from log line
                # Format: "HH:mm:ss | LEVEL    | message"
                tag = "INFO"
                if " | " in log_line:
                    parts = log_line.split(" | ")
                    if len(parts) >= 2:
                        level_part = parts[1].strip()
                        if level_part.startswith("SUCCESS"):
                            tag = "SUCCESS"
                        elif level_part.startswith("WARNING"):
                            tag = "WARNING"
                        elif level_part.startswith("ERROR"):
                            tag = "ERROR"
                        elif level_part.startswith("DEBUG"):
                            tag = "DEBUG"

                self.text.insert(tk.END, log_line + "\n", tag)

            self.text.see(tk.END)  # Auto-scroll to bottom
            self.text.config(state=tk.DISABLED)

        # Schedule next poll
        self.after(100, self.poll_logs)

    def clear(self):
        """Clear all logs."""
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def start_polling(self):
        """Start polling for logs."""
        self.after(100, self.poll_logs)
