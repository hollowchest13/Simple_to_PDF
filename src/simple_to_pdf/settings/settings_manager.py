import logging
import json
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SettingsManager:
    def __init__(self, *, settings_path: Path, default_settings: Dict[str, str]):
        self.settings_path = settings_path
        self.default_settings: Dict[str, str] = default_settings

    def save_settings(self, settings: Dict[str, str]):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

    def get_settings(self) -> Dict[str, str]:
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return self.default_settings
