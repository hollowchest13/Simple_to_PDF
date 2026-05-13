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
    _LANG_MAP = {"English": "en", "Українська": "uk", "Deutsch": "de", "Polski": "pl"}

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
        # Add logging
        print(f"Switching to {target_lang}. Total observers: {len(cls._observers)}")

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
        if section:
            target_section = section
        else:
            target_section = getattr(self, "loc_section", "ui")

        lang_data = self._translations.get(self._current_lang, {})

        # 1. Склеюємо секцію і ключ в один повний шлях
        full_path = f"{target_section}.{key}"

        # 2. Проходимо по всьому шляху крок за кроком
        data = lang_data
        parts = full_path.split(".")

        for i, part in enumerate(parts):
            if isinstance(data, dict) and part in data:
                data = data[part]

        # 3. Якщо результат — рядок, форматуємо його
        if isinstance(data, str):
            try:
                return data.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                return data

        return key

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
        EXCLUDED_KEYS = {"language_selector"}
        for key, widget in widgets_dict.items():
            if key in EXCLUDED_KEYS:
                continue
            if widget == self or not hasattr(widget, "configure"):
                continue

            try:
                new_text = self.get_text(key, section=section)

                # Standard text (buttons, labels)
                try:
                    self.update_widget_with_adaptive_font(
                        widget=widget, new_text=new_text, threshold=16
                    )
                    continue  # If it worked, moving on to the next widget.
                except Exception:
                    pass

                # Container header (Your CTkListbox / ScrollableFrame)
                try:
                    widget.configure(label_text=new_text)
                    continue
                except Exception:
                    pass

                # Input Hint (Entry / Textbox)
                try:
                    widget.configure(placeholder_text=new_text)
                except Exception:
                    pass

            except Exception as e:
                logging.debug(f"Error updating widget '{key}': {e}")

    def update_widget_with_adaptive_font(
        self, widget: Any, new_text: str, threshold: int
    ):
        """
        Dynamically updates widget text and adjusts font size based on text length.
        """
        try:
            # 1. If a widget doesn't have a 'text' attribute, we don't need it.
            try:
                widget.configure(text=new_text)
            except Exception:
                return

            # Get base font size
            base_size = getattr(widget, "base_font_size", None)

            if base_size is None:
                try:
                    current_font = widget.cget("font")
                    # Extracting the size based on what cget returned
                    if hasattr(current_font, "cget"):
                        base_size = int(current_font.cget("size"))
                    elif isinstance(current_font, (list, tuple)):
                        base_size = int(current_font[1])
                    else:
                        # Attempting to parse the string."
                        base_size = int(str(current_font).split()[1])
                except:
                    base_size = 13  # Default if unable to determine.

                widget.base_font_size = base_size

            # 3. Calculating the new size.
            reduction = max(0, (len(new_text) - threshold) // 2)
            new_size = max(base_size - reduction, 10)

            # 4. Font updating
            try:
                current_font = widget.cget("font")
                if hasattr(current_font, "cget"):
                    family = current_font.cget("family")
                    # Checking the font style (bold/italic).
                    weight = current_font.cget("weight")
                    new_font = (family, new_size, weight)
                elif isinstance(current_font, (list, tuple)):
                    new_font = (current_font[0], new_size, *current_font[2:])
                else:
                    new_font = ("Segoe UI", new_size)

                widget.configure(font=new_font)
            except Exception:
                # If the widget supports text but not fonts
                pass

        except Exception as e:
            # Останній рубіж — просто виводимо помилку в консоль, щоб не "класти" GUI
            print(f"Critical font error: {e}")

    def _get_adaptive_font_size(
        self, text: str, threshold: int = 14, base_size: int | None = 14
    ) -> int | None:
        if base_size == None:
            return None
        lenght = len(text)
        if lenght <= threshold:
            return base_size
        reduction = (lenght - threshold) // 4
        return max(base_size - reduction, 10)

    def refresh_localization(self) -> None:

        section = getattr(self, "loc_section", None)
        widgets = getattr(self, "ui", None)

        if section and isinstance(widgets, dict):
            self.update_widgets_text(widgets, section=section)

    def remove_from_observers(self):
        if self in self._observers:
            self._observers.remove(self)
