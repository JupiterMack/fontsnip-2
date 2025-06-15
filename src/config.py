# src/config.py

"""
Handles application configuration.

Manages loading and saving settings, such as the global hotkey combination
and OCR confidence threshold. Provides default values if no user configuration
exists. A singleton instance `config` is exported for use across the application.
"""

import json
import os
import sys
from pathlib import Path

# --- Constants ---

# Application name used for creating a dedicated config directory
APP_NAME = "FontSnip"

# Name of the configuration file
CONFIG_FILE_NAME = "config.json"

# Name of the pre-computed font database file
FONT_DATABASE_FILE = "font_features.pkl"


# --- Helper Function for Path Management ---

def get_app_dir() -> Path:
    """
    Gets the application's data directory in a cross-platform way.

    This ensures that configuration and data files are stored in the standard
    location for the user's operating system.

    - Windows: %APPDATA%/FontSnip
    - macOS:   ~/Library/Application Support/FontSnip
    - Linux:   ~/.config/FontSnip (following XDG Base Directory Specification)

    Returns:
        Path: A pathlib.Path object pointing to the application directory.
    """
    if sys.platform == "win32":
        # APPDATA is the standard location for user-specific app data on Windows
        app_data = os.getenv("APPDATA")
        if app_data:
            return Path(app_data) / APP_NAME
    elif sys.platform == "darwin":
        # Standard location for application support files on macOS
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        # Standard XDG Base Directory Specification for Linux/other Unix-likes
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home:
            return Path(xdg_config_home) / APP_NAME
        else:
            return Path.home() / ".config" / APP_NAME

    # Fallback to a simple home directory folder if all else fails
    return Path.home() / f".{APP_NAME.lower()}"


# --- Main Configuration Class ---

class ConfigManager:
    """
    Manages loading and saving application settings from a JSON file.

    This class provides a single point of access for all configuration values.
    It handles loading settings from a file and provides default values
    if the file does not exist or a key is missing.
    """
    def __init__(self):
        """Initializes the ConfigManager, defines defaults, and loads settings."""
        # --- Default Configuration Values ---
        self._defaults = {
            "hotkey": "<ctrl>+<alt>+s",
            "ocr_confidence_threshold": 60,
            "image_upscaling_factor": 2,
            "top_n_matches": 3,
            "ocr_languages": ["en"],
            "enable_denoising": False
        }

        # --- Path Configuration ---
        self.app_dir = get_app_dir()
        self.config_path = self.app_dir / CONFIG_FILE_NAME
        self.font_database_path = self.app_dir / FONT_DATABASE_FILE

        # --- Load and Apply Configuration ---
        self._config = self._defaults.copy()
        self.load_config()

    def load_config(self):
        """
        Loads configuration from the JSON file. If the file doesn't exist,
        it will be created with default values.
        """
        self.app_dir.mkdir(parents=True, exist_ok=True)
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Update defaults with user settings, ensuring no keys are missing
                self._config.update(user_config)
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not parse config file at {self.config_path}. Using defaults.")
                # If the file is corrupt, save the defaults over it to fix it
                self.save_config()
        else:
            # If the file doesn't exist, create it with the defaults
            self.save_config()

    def save_config(self):
        """Saves the current configuration to the JSON file."""
        self.app_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4)
        except IOError as e:
            print(f"Error: Could not write to config file at {self.config_path}: {e}")

    def get(self, key: str, default=None):
        """Gets a configuration value by key."""
        return self._config.get(key, default)

    def set(self, key: str, value):
        """Sets a configuration value and saves it to the file."""
        self._config[key] = value
        self.save_config()

    # --- Properties for easy, read-only access from other modules ---

    @property
    def HOTKEY(self) -> str:
        """The global hotkey combination to trigger capture mode."""
        return self.get("hotkey")

    @property
    def OCR_CONFIDENCE_THRESHOLD(self) -> int:
        """The minimum confidence score (0-100) for OCR results to be considered."""
        return self.get("ocr_confidence_threshold")

    @property
    def IMAGE_UPSCALING_FACTOR(self) -> int:
        """The factor by which the captured image is upscaled before OCR."""
        return self.get("image_upscaling_factor")

    @property
    def TOP_N_MATCHES(self) -> int:
        """The number of top font matches to display in the results."""
        return self.get("top_n_matches")

    @property
    def OCR_LANGUAGES(self) -> list[str]:
        """List of languages for EasyOCR to use (e.g., ['en'])."""
        return self.get("ocr_languages")

    @property
    def ENABLE_DENOISING(self) -> bool:
        """Whether to apply a denoising filter during image preprocessing."""
        return self.get("enable_denoising")


# --- Singleton Instance ---
# This instance is created once and imported by other modules to ensure
# consistent access to the application's configuration.
config = ConfigManager()


# --- Example Usage (for testing this file directly) ---
if __name__ == '__main__':
    print("--- FontSnip Configuration Manager ---")
    print(f"Application Directory: {config.app_dir}")
    print(f"Configuration File: {config.config_path}")
    print(f"Font Database File: {config.font_database_path}")
    print("\n--- Current Settings ---")
    print(f"Hotkey: {config.HOTKEY}")
    print(f"OCR Confidence Threshold: {config.OCR_CONFIDENCE_THRESHOLD}")
    print(f"Image Upscaling Factor: {config.IMAGE_UPSCALING_FACTOR}")
    print(f"Top N Matches: {config.TOP_N_MATCHES}")
    print(f"OCR Languages: {config.OCR_LANGUAGES}")
    print(f"Denoising Enabled: {config.ENABLE_DENOISING}")

    # Example of changing a setting
    print("\n--- Testing set() ---")
    original_threshold = config.OCR_CONFIDENCE_THRESHOLD
    print(f"Changing OCR threshold to 75...")
    config.set("ocr_confidence_threshold", 75)
    print(f"New value from property: {config.OCR_CONFIDENCE_THRESHOLD}")
    print("Reloading config from disk to verify persistence...")
    new_config_instance = ConfigManager()
    print(f"Value after reload: {new_config_instance.OCR_CONFIDENCE_THRESHOLD}")

    # Revert the change for subsequent test runs
    print(f"\nReverting OCR threshold to {original_threshold}...")
    config.set("ocr_confidence_threshold", original_threshold)
    print("Done.")
```