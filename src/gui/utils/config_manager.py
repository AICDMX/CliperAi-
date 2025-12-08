"""Configuration manager for GUI settings and API keys."""

import json
import os
from pathlib import Path
from dotenv import load_dotenv, set_key


class GUIConfigManager:
    """Manage GUI-specific settings persisted in ~/.cliper_gui_config.json."""

    def __init__(self):
        """Initialize configuration manager."""
        self.config_file = Path.home() / ".cliper_gui_config.json"
        self.config = self.load()

    def load(self):
        """Load GUI configuration from file or return defaults."""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except Exception:
                return self.get_defaults()
        return self.get_defaults()

    def get_defaults(self):
        """Get default configuration."""
        return {
            "window_geometry": "1200x800",
            "last_output_dir": str(Path.home() / "Downloads"),
            "default_whisper_model": "base",
            "default_aspect_ratio": "original",
            "enable_subtitles": True,
        }

    def save(self):
        """Save current configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set configuration value and save."""
        self.config[key] = value
        self.save()


class PipelineConfigManager:
    """Manage pipeline configuration from .env file."""

    def __init__(self):
        """Initialize pipeline config manager by loading .env."""
        load_dotenv()

    def get_api_key(self):
        """Get Google API key from environment."""
        return os.getenv("GOOGLE_API_KEY")

    def set_api_key(self, api_key: str):
        """Set Google API key in .env file."""
        env_file = Path.cwd() / ".env"
        if not env_file.exists():
            env_file.write_text("GOOGLE_API_KEY=\n")
        set_key(str(env_file), "GOOGLE_API_KEY", api_key)
        # Update environment
        os.environ["GOOGLE_API_KEY"] = api_key

    def get_default_whisper_model(self):
        """Get default Whisper model from environment."""
        return os.getenv("WHISPER_MODEL", "base")

    def get_default_whisper_language(self):
        """Get default Whisper language from environment."""
        return os.getenv("WHISPER_LANGUAGE", "auto")

    def get_default_min_clip_duration(self):
        """Get default minimum clip duration from environment."""
        try:
            return int(os.getenv("MIN_CLIP_DURATION", "30"))
        except ValueError:
            return 30

    def get_default_max_clip_duration(self):
        """Get default maximum clip duration from environment."""
        try:
            return int(os.getenv("MAX_CLIP_DURATION", "120"))
        except ValueError:
            return 120

    def get_default_max_clips(self):
        """Get default maximum number of clips from environment."""
        try:
            return int(os.getenv("MAX_CLIPS", "20"))
        except ValueError:
            return 20

    def validate_api_key(self):
        """
        Check if Google API key is configured.

        Raises:
            ValueError: If API key is not set

        """
        if not self.get_api_key():
            raise ValueError(
                "Google API key not configured. Go to Settings > Configure API Key"
            )

    def validate_pipeline(self):
        """
        Validate that all required pipeline configuration is present.

        Raises:
            ValueError: If any required config is missing

        """
        self.validate_api_key()
