import logging
from pathlib import Path
from PIL import Image
from customtkinter import CTkImage
from typing import Any, Dict, Optional
from simple_to_pdf.widgets.base_widgets import BaseTextBox
from simple_to_pdf.core.config import BASE_PATH
from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton, BaseLabel

logger = logging.getLogger(__name__)


class InfoDialog(BaseDialog):
    """
    A dialog designed to display scrollable text content such as
    licenses, logs, or detailed descriptions.
    """

    def __init__(
        self,
        parent: Any,
        text: str,
        title_key: str = "info",
        header_key: Optional[str] = None,
        btn_key: str = "btns.btn_close",
        size: str = "700x500",
        text_font: str = "Segoe UI",
        font_size: int = 16,
        icon_type: Optional[str] = None,
        **kwargs,
    ):
        # We target notifications section in JSON
        super().__init__(parent, title_key=title_key, loc_section="ui.notifications")

        # Hybrid logic: checks if 'text' exists in messages, else uses raw text
        localized_content = self.get_text(f"messages.{text}")
        if localized_content != f"messages.{text}":
            self.raw_text = (
                localized_content.format(**kwargs) if kwargs else localized_content
            )
        else:
            self.raw_text = text

        self.header_key = header_key
        self.btn_key = btn_key
        self.icons = self._init_icons()
        self.current_icon = self._load_icon(icon_type=icon_type)

        if size:
            self.geometry(size)

        self._setup_dialog_ui(text_font, font_size)
        self.refresh_localization()

    def _load_icon(self, *, icon_type: Optional[str] = None) -> Optional[CTkImage]:
        if icon_type is None:
            return None

        raw_path = self.icons.get(icon_type)
        if not raw_path:
            return None

        icon_path = Path(raw_path)
        if icon_path.is_file():
            try:
                return CTkImage(light_image=Image.open(icon_path), size=(60, 60))
            except (IOError, SyntaxError) as e:
                logger.error(f"Could not load icon {icon_type}: {e}")
        return None

    def _init_icons(self) -> Dict[str, str]:
        # Cross-platform path handling
        base_path = Path(BASE_PATH) / "icons"
        return {
            "info": str(base_path / "info.png"),
            "error": str(base_path / "error.png"),
            "success": str(base_path / "success.png"),
            "warning": str(base_path / "warning.png"),
        }

    def _setup_dialog_ui(self, font_name: str, font_size: int) -> None:
        """Constructs the UI and registers elements for localization."""

        # Header area: Optional icon + Dynamic Title
        if self.current_icon:
            self.icon_label = BaseLabel(self.header, text="", image=self.current_icon)
            self.icon_label.pack(side="left", padx=(25, 0), pady=(25, 10))

        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].pack(expand=True, pady=(25, 10))

        # Main scrollable text content
        self.txt = BaseTextBox(
            self.content, textbox_type="info", font=(font_name, font_size)
        )
        self.txt.insert("1.0", self.raw_text)
        self.txt.configure(state="disabled")
        self.txt.pack(expand=True, fill="both", padx=15, pady=10)

        # Footer: Action button
        self.ui["btn_close"] = PrimaryButton(
            self.footer, text="", command=self._on_close, height=40, width=120
        )
        self.ui["btn_close"].pack(side="right", padx=25, pady=15)

    def refresh_localization(self) -> None:
        """Updates static UI elements while preserving dynamic text content."""
        super().refresh_localization()

        # Update header specifically if a key was provided (e.g., 'headers.license_header')
        if "header_title" in self.ui and self.header_key is not None:
            self.ui["header_title"].configure(text=self.get_text(self.header_key))
        
        if "btn_close" in self.ui:
            self.ui["btn_close"].configure(text=self.get_text(self.btn_key))

    def _on_close(self):
        """Standard cleanup: ensure observer removal before destruction."""
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()
