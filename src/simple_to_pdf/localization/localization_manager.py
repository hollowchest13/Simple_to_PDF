import json
from pathlib import Path
from typing import Dict, Any, List


class LocalizationManager:
    def __init__(self, default_lang: str = "English") -> None:
        self.translations_dir: Path = Path(__file__).parent.parent / "lang"
        self.current_lang: str = default_lang
        self._data: Dict[str, Dict[str, str]] = {}
        self._load_all_translations()

    def _load_all_translations(self) -> None:
        if not self.translations_dir.exists():
            self.translations_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.translations_dir.glob("*.json"):
            lang_name: str = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._data[lang_name] = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

    def get_text(self, key: str, **kwargs: Any) -> str:
        translations = self._data.get(self.current_lang, {})
        template = translations.get(key, key)
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template

    def get_available_languages(self) -> List[str]:
        return sorted(list(self._data.keys()))

    def set_language(self, lang: str) -> None:
        if lang in self._data:
            self.current_lang = lang