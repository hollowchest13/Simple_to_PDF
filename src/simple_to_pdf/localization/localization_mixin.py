import json
import logging
from pathlib import Path
from typing import Dict, Any, List


class LocalizationMixin:
    """
    Mixin for UI localization using an Observer pattern.
    """

    _translations: Dict[str, Dict[str, Any]] = {}
    _current_lang: str = "en"
    _lang_dir: Path = Path(__file__).parent.parent / "lang"
    _observers: List[Any] = []
    _LANG_MAP = {"English": "en", "Ukrainian": "uk", "Українська": "uk"}

    @classmethod
    def load_translations(cls) -> None:
        """Loads all JSON translation files from the lang directory."""
        if not cls._lang_dir.exists():
            cls._lang_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in cls._lang_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._translations[file_path.stem] = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load {file_path.name}: {e}")

    @classmethod
    def switch_language(cls, lang_name: str) -> None:
        """Sets the current language and notifies all registered observers."""
        target_lang = cls._LANG_MAP.get(lang_name, lang_name)
        print(
            f"Switching to {target_lang}. Total observers: {len(cls._observers)}"
        )  # Для тесту

        if target_lang in cls._translations:
            cls._current_lang = target_lang
            logging.info(f"Language switched to: {target_lang}")
            cls._notify_observers()
        else:
            logging.warning(f"Translation not found for: {target_lang}")

    @classmethod
    def _notify_observers(cls):
        """Triggers refresh_localization on all subscribed components."""
        for observer in cls._observers:
            if hasattr(observer, "refresh_localization"):
                try:
                    observer.refresh_localization()
                except Exception as e:
                    logging.error(f"Error refreshing {observer}: {e}")

    def init_localization(self):
        """Registers the current instance as an observer for language changes."""
        if self not in self.__class__._observers:
            self.__class__._observers.append(self)

    def get_text(self, key: str, section: str | None = None, **kwargs: Any) -> str:
        """Retrieves translated text, prioritizing self.loc_section."""

        # 1. Визначаємо цільову секцію:
        # спочатку аргумент, потім атрибут екземпляра, в кінці - дефолт "ui"
        if section:
            target_section = section
        else:
            target_section = getattr(self, "loc_section", "ui")

        lang_data = self._translations.get(self._current_lang, {})
        section_data = lang_data

        # 2. Навігація по вкладених секціях (ui.about_dialog)
        for part in target_section.split("."):
            if isinstance(section_data, dict):
                # Використовуємо .get(), щоб не "впасти", якщо секції немає
                section_data = section_data.get(part, {})
            else:
                section_data = {}

        # 3. Отримуємо шаблон. Якщо його немає в секції - повертаємо назву ключа
        template = section_data.get(key, key) if isinstance(section_data, dict) else key

        # Гарантуємо, що це рядок, щоб уникнути помилок типізації
        template_str = str(template)

        # 4. Форматування (підстановка {version}, {engine} тощо)
        try:
            # .format() проігнорує kwargs, якщо в рядку немає дужок {}
            return template_str.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            # Якщо в JSON є {placeholder}, але ти не передав його в kwargs - повернемо як є
            return template_str

    def get_available_languages(self) -> List[str]:
        """Returns list of human-readable language names for UI menus."""
        reverse_map = {v: k for k, v in self._LANG_MAP.items()}
        return [
            reverse_map.get(code, code.capitalize())
            for code in self._translations.keys()
        ]

    def update_widgets_text(self, widgets_dict: Dict[str, Any], section: str) -> None:
        """
        Updates text-related properties of widgets.
        Tries 'text', then 'label_text', then 'placeholder_text'.
        """
        for key, widget in widgets_dict.items():
            if widget == self or not hasattr(widget, "configure"):
                continue

            try:
                new_text = self.get_text(key, section=section)

                # Спроба 1: Стандартний текст (кнопки, лейбли)
                try:
                    widget.configure(text=new_text)
                    continue  # Якщо спрацювало, переходимо до наступного віджета
                except Exception:
                    pass

                # Спроба 2: Заголовок контейнера (Твій CTkListbox / ScrollableFrame)
                try:
                    widget.configure(label_text=new_text)
                    continue
                except Exception:
                    pass

                # Спроба 3: Підказка (Entry / Textbox)
                try:
                    widget.configure(placeholder_text=new_text)
                except Exception:
                    pass

            except Exception as e:
                logging.debug(f"Error updating widget '{key}': {e}")

    def refresh_localization(self) -> None:
    
        # getattr знайде актуальний self.ui, навіть якщо він був перезаписаний
        section = getattr(self, "loc_section", None)
        widgets = getattr(self, "ui", None)

        if section and isinstance(widgets, dict):
            self.update_widgets_text(widgets, section=section)

    def remove_from_observers(self):
        if self in self._observers:
            self._observers.remove(self)
