import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SettingsManager:
    def __init__(self, *, settings_path: Path, default_settings: dict[str, str]):
        self.settings_path = settings_path
        self.default_settings: dict[str, str] = default_settings

    def save_settings(self, settings: dict[str, str]):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

    def get_settings(self) -> dict[str, str]:
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError, FileNotFoundError):
            return self.default_settings
