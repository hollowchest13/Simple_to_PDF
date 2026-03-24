import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional


class LocalizationMixin:
    """
    Міксин для локалізації. Тепер він сам керує оновленням підписаних віджетів.
    """

    _translations: Dict[str, Dict[str, Any]] = {}
    _current_lang: str = "en"  # Дефолт має збігатися з назвою файлу (en.json)
    _lang_dir: Path = Path(__file__).parent.parent / "lang"

    # Список об'єктів (frames/windows), які хочуть оновлюватися автоматично
    _observers: List[Any] = []

    # Мапа для перетворення назв з UI в коди файлів
    _LANG_MAP = {"English": "en", "Ukrainian": "uk", "Українська": "uk"}

    @classmethod
    def load_translations(cls) -> None:
        """Завантажує всі JSON файли з папки lang."""
        if not cls._lang_dir.exists():
            cls._lang_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in cls._lang_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._translations[file_path.stem] = json.load(f)
            except Exception as e:
                logging.error(f"Помилка завантаження {file_path.name}: {e}")

    @classmethod
    def set_language(cls, lang_name: str) -> None:
        """
        Встановлює мову та автоматично оновлює всі підписані компоненти.
        lang_name може бути як 'en', так і 'Ukrainian'.
        """
        # Перетворюємо "Ukrainian" -> "uk", якщо потрібно
        target_lang = cls._LANG_MAP.get(lang_name, lang_name)

        if target_lang in cls._translations:
            cls._current_lang = target_lang
            logging.info(f"Language changed to: {target_lang}")

            # Оновлюємо всіх, хто підписався
            cls._notify_observers()
        else:
            logging.warning(f"Language file for '{target_lang}' not found.")

    @classmethod
    def _notify_observers(cls):
        """Викликає метод refresh_localization у всіх підписників."""
        for observer in cls._observers:
            if hasattr(observer, "refresh_localization"):
                try:
                    observer.refresh_localization()
                except Exception as e:
                    logging.error(f"Error refreshing {observer}: {e}")

    def init_localization(self):
        """Реєструє поточний об'єкт (self) на оновлення мови."""
        if self not in self.__class__._observers:
            self.__class__._observers.append(self)

    def get_text(self, key: str, section: str = "ui", **kwargs: Any) -> str:
        """Повертає перекладений текст, підтримує вкладеність через крапку."""
        lang_data = self._translations.get(self._current_lang, {})

        # Прохід по вкладених секціях (напр. "ui.buttons")
        section_data = lang_data
        for part in section.split("."):
            if isinstance(section_data, dict):
                section_data = section_data.get(part, {})
            else:
                section_data = {}

        template = section_data.get(key, key) if isinstance(section_data, dict) else key

        try:
            return template.format(**kwargs)
        except Exception:
            return template

    def log_msg(self, key: str, level: str = "info", **kwargs: Any) -> str:
        message = self.get_text(key, section="msg", **kwargs)
        log_func = getattr(logging, level.lower(), logging.info)
        log_func(f"[{self.__class__.__name__}] {message}")
        return message

    def get_available_languages(self) -> List[str]:
        """Повертає список назв для OptionMenu (English, Ukrainian тощо)."""
        # Створюємо зворотну мапу для гарних назв
        reverse_map = {v: k for k, v in self._LANG_MAP.items()}
        codes = self._translations.keys()
        return [reverse_map.get(code, code.capitalize()) for code in codes]

    def update_widgets_text(
        self, widgets_dict: Dict[str, Any], section: str = "ui.buttons"
    ) -> None:
        """
        Універсальний метод для оновлення тексту у віджетах.
        Приймає словник {ID_перекладу: об'єкт_віджета}.
        """
        for key, widget in widgets_dict.items():
            if hasattr(widget, "configure"):
                new_text = self.get_text(key, section=section)
                widget.configure(text=new_text)

        # Додай це у свій LocalizationMixin

    def refresh_localization(self) -> None:
        # Список усіх назв словників, які ти використовуєш у різних панелях
        # Додаємо сюди ті назви, що ми бачили у PDFMergerGUI

        # 1. Оновлюємо кнопки
        for attr in ["btns", "list_controls", "help_controls"]:
            data = getattr(self, attr, None)
            if isinstance(data, dict):
                self.update_widgets_text(data, section="ui.buttons")

        # 2. Оновлюємо налаштування/контроли
        for attr in ["controls", "settings_controls"]:
            data = getattr(self, attr, None)
            if isinstance(data, dict):
                self.update_widgets_text(data, section="ui.settings")
