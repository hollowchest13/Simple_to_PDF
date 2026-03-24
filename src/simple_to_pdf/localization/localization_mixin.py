import json
import logging
from pathlib import Path
from typing import Dict, Any, List


class LocalizationMixin:
    """
    A Mixin to provide localization and logging capabilities to UI frames and logic classes.
    Uses class-level attributes to share translation data across all instances.
    """

    _translations: Dict[str, Dict[str, Any]] = {}
    _current_lang: str = "en"
    _lang_dir: Path = Path(__file__).parent.parent / "lang"

    @classmethod
    def load_translations(cls) -> None:
        """
        Scans the 'lang' directory and loads all JSON files into memory.
        Should be called once at application startup.
        """
        if not cls._lang_dir.exists():
            cls._lang_dir.mkdir(parents=True, exist_ok=True)
            logging.warning(f"Localization directory created at {cls._lang_dir}")
            return

        for file_path in cls._lang_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._translations[file_path.stem] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Failed to load translation file {file_path.name}: {e}")

    @classmethod
    def set_language(cls, lang: str) -> None:
        """
        Updates the global language for all classes using this Mixin.
        """
        if lang in cls._translations:
            cls._current_lang = lang
            logging.info(f"Language changed to: {lang}")

    def get_text(self, key: str, section: str = "ui", **kwargs: Any) -> str:
        """
        Тепер підтримує вкладені секції, наприклад section="ui.buttons"
        """
        # 1. Отримуємо дані для поточної мови
        lang_data = self._translations.get(self._current_lang, {})

        # 2. Проходимо по вкладених секціях (ui -> buttons)
        section_data = lang_data
        for part in section.split("."):
            if isinstance(section_data, dict):
                section_data = section_data.get(part, {})
            else:
                section_data = {}

        # 3. Шукаємо сам ключ
        template = section_data.get(key, key) if isinstance(section_data, dict) else key

        # 4. Форматуємо, якщо є змінні {name}
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template

    def log_msg(self, key: str, level: str = "info", **kwargs: Any) -> str:
        """
        Translates a message, logs it to the system log, and returns the string.
        Useful for status updates and error reporting.
        """
        message = self.get_text(key, section="msg", **kwargs)

        log_func = getattr(logging, level.lower(), logging.info)
        # Includes the class name of the caller for better debugging
        log_func(f"[{self.__class__.__name__}] {message}")

        return message

    def get_available_languages(self) -> List[str]:
        """
        Returns a sorted list of language names based on available JSON files.
        """
        return sorted(list(self._translations.keys()))
