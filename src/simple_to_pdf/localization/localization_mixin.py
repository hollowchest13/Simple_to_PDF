import logging
import json
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class LocalizationMixin:
    """
    Mixin for UI localization using an Observer pattern.
    """

    _translations: Dict[str, Dict[str, Any]] = {}
    _current_lang: str = "en"
    _lang_dir: Path = Path(__file__).parent.parent / "lang"
    _observers: List[Any] = []
    _LANG_MAP: Dict[str, str] = {}

    @classmethod
    def load_translations(cls) -> None:
        """Loads all JSON translation files and builds the language map."""

        if not cls._lang_dir.exists():
            cls._lang_dir.mkdir(parents=True, exist_ok=True)
            return

        # Clear translations
        cls._translations = {}
        cls._LANG_MAP = {}

        for file_path in cls._lang_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    lang_code = file_path.stem

                    # Saving translating data
                    cls._translations[lang_code] = data
                    lang_name = data.get("info", {}).get(
                        "lang_name", lang_code.capitalize()
                    )
                    cls._LANG_MAP[lang_name] = lang_code

            except Exception as e:
                logger.error(f"Failed to load {file_path.name}: {e}")

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
        Main entry point for updating UI localization.
        Iterates through widgets and applies translation.
        """
        EXCLUDED_KEYS = {"language_selector"}

        for key, widget in widgets_dict.items():
            if (
                key in EXCLUDED_KEYS
                or widget == self
                or not hasattr(widget, "configure")
            ):
                continue

            new_text = self.get_text(key, section=section)
            self._apply_text_to_widget(key, widget, new_text)

    def _apply_text_to_widget(self, key: str, widget: Any, text: str) -> None:
        """
        Determines the correct attribute to update based on widget type and attributes.
        """
        try:
            # 1. Handle Buttons with Adaptive Font
            if self._is_button_widget(widget):
                if self.update_widget_with_adaptive_font(widget, text, threshold=16):
                    return

            # 2. Standard 'text' attribute (Labels, Checkboxes)
            if self._try_configure(widget, text=text):
                return

            # 3. Container 'label_text' (ScrollableFrame, Listbox)
            if self._try_configure(widget, label_text=text):
                return

            # 4. Input 'placeholder_text' (Entry, Textbox)
            if self._try_configure(widget, placeholder_text=text):
                return

            logger.debug(
                f"Widget '{key}' ({type(widget).__name__}) has no supported text attribute."
            )

        except Exception as e:
            logger.error(f"Error updating widget '{key}': {e}")

    def _is_button_widget(self, widget: Any) -> bool:
        """Returns True if the widget is a button-like component."""
        return "button" in widget.__class__.__name__.lower()

    def _try_configure(self, widget: Any, **kwargs) -> bool:
        """Safe wrapper for widget.configure(). Returns True if successful."""
        try:
            widget.configure(**kwargs)
            return True
        except Exception:
            return False

    def update_widget_with_adaptive_font(
        self, widget: Any, new_text: str, threshold: int
    ) -> bool:
        """
        Sets text and adjusts font size. Specialized for button-like widgets.
        """
        if not self._try_configure(widget, text=new_text):
            return False

        base_size = self._get_or_store_base_font_size(widget)
        new_size = self._calculate_adaptive_size(new_text, base_size, threshold)

        self._apply_font_size(widget, new_size)
        return True

    def _get_or_store_base_font_size(self, widget: Any) -> int:
        """Retrieves or initializes the original font size for the widget."""
        # 1. Check if we already cached it
        base_size = getattr(widget, "base_font_size", None)
        if base_size is not None:
            return base_size

        try:
            # 2. Safely get the font object
            current_font = None
            if hasattr(widget, "cget"):
                current_font = widget.cget("font")

            # 3. Handle the case where current_font is None
            if current_font is None:
                base_size = 13  # Default fallback

            # 4. Extract size based on type (Object, Tuple, or String)
            elif hasattr(current_font, "cget"):  # CTkFont or similar object
                base_size = int(current_font.cget("size"))

            elif isinstance(current_font, (list, tuple)) and len(current_font) > 1:
                base_size = int(current_font[1])

            else:
                # String parsing: e.g., "Arial 14 bold"
                parts = str(current_font).split()
                # Check if the second part is actually a number
                if len(parts) > 1 and parts[1].replace("-", "").isdigit():
                    base_size = int(parts[1])
                else:
                    base_size = 13

        except Exception as e:
            logger.debug(f"Could not determine font size for {widget}: {e}")
            base_size = 13

        # Store it so we don't have to calculate this mess again
        widget.base_font_size = base_size
        return base_size

    def _calculate_adaptive_size(
        self, text: str, base_size: int, threshold: int
    ) -> int:
        """Logic for decreasing font size based on text length."""
        reduction = max(0, (len(text) - threshold) // 2)
        return max(base_size - reduction, 10)

    def _apply_font_size(self, widget: Any, new_size: int) -> None:
        """Safely applies a new size to the existing widget font."""
        try:
            current_font = widget.cget("font")
            if hasattr(current_font, "cget"):
                new_font = (
                    current_font.cget("family"),
                    new_size,
                    current_font.cget("weight"),
                )
            elif isinstance(current_font, (list, tuple)):
                new_font = (current_font[0], new_size, *current_font[2:])
            else:
                new_font = ("Segoe UI", new_size)

            widget.configure(font=new_font)
        except Exception as e:
            logger.debug(f"Could not update font for {widget}: {e}")

    def refresh_localization(self) -> None:

        section = getattr(self, "loc_section", None)
        widgets = getattr(self, "ui", None)

        if section and isinstance(widgets, dict):
            self.update_widgets_text(widgets, section=section)

    def remove_from_observers(self):
        if self in self._observers:
            self._observers.remove(self)
