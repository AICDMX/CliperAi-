#!/usr/bin/env python3
"""
CLIPER GUI - Tkinter interface for AI-powered video clip generation

Usage:
    python cliper_gui.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.main_window import MainWindow
from src.gui.utils.logger_bridge import LoggerBridge


def main():
    """Run the CLIPER GUI application."""
    # Setup logger bridge first to capture all logs
    logger_bridge = LoggerBridge()
    logger_bridge.setup()

    # Create and run GUI
    app = MainWindow(logger_bridge)
    app.run()


if __name__ == "__main__":
    main()
