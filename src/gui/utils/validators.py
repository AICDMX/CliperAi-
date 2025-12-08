"""Input validation utilities for GUI."""

import re
from pathlib import Path
from typing import Optional


class Validators:
    """Collection of input validation methods."""

    @staticmethod
    def validate_youtube_url(url: str) -> None:
        """
        Validate YouTube URL format.

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL is not a valid YouTube link

        """
        if not url or not url.strip():
            raise ValueError("YouTube URL cannot be empty")

        pattern = r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+"
        if not re.search(pattern, url):
            raise ValueError(
                "Invalid YouTube URL. Must be youtube.com or youtu.be link"
            )

    @staticmethod
    def validate_logo_path(path: Optional[str]) -> None:
        """
        Validate logo file path.

        Args:
            path: Path to logo file

        Raises:
            ValueError: If file doesn't exist or isn't valid image format

        """
        if not path or not path.strip():
            # Empty is ok (logo is optional)
            return

        path_obj = Path(path)
        if not path_obj.exists():
            raise ValueError(f"Logo file not found: {path}")

        if not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            raise ValueError("Logo must be PNG, JPG, GIF, or BMP format")

    @staticmethod
    def validate_output_directory(path: Optional[str]) -> None:
        """
        Validate output directory exists and is writable.

        Args:
            path: Directory path

        Raises:
            ValueError: If directory doesn't exist or isn't writable

        """
        if not path or not path.strip():
            raise ValueError("Output directory cannot be empty")

        path_obj = Path(path)
        if not path_obj.exists():
            raise ValueError(f"Output directory does not exist: {path}")

        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        # Check if writable by trying to write a test file
        try:
            test_file = path_obj / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception:
            raise ValueError(f"Output directory is not writable: {path}")

    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> None:
        """
        Validate Google API key format.

        Args:
            api_key: API key string

        Raises:
            ValueError: If API key is invalid

        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")

        api_key = api_key.strip()
        # Google API keys are typically long alphanumeric strings
        if len(api_key) < 20:
            raise ValueError("API key seems too short to be valid")

    @staticmethod
    def validate_numeric_range(
        value: int, min_val: int, max_val: int, field_name: str = "Value"
    ) -> None:
        """
        Validate numeric value is within range.

        Args:
            value: Value to check
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Name of field for error message

        Raises:
            ValueError: If value is outside range

        """
        if value < min_val or value > max_val:
            raise ValueError(
                f"{field_name} must be between {min_val} and {max_val}, got {value}"
            )

    @staticmethod
    def validate_duration_range(min_duration: int, max_duration: int) -> None:
        """
        Validate clip duration range.

        Args:
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds

        Raises:
            ValueError: If range is invalid

        """
        if min_duration <= 0:
            raise ValueError("Minimum duration must be greater than 0")

        if max_duration <= 0:
            raise ValueError("Maximum duration must be greater than 0")

        if min_duration >= max_duration:
            raise ValueError(
                f"Minimum duration ({min_duration}s) must be less than maximum ({max_duration}s)"
            )
