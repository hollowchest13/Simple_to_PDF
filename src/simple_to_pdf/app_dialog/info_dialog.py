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
    A versatile dialog for displaying content based on predefined scenarios.
    It automatically links titles, headers, and buttons from the localization JSON.
    """

    def __init__(
        self,
        parent: Any,
        scenario_key: str = "info",
        text_font: str = "Consolas",
        font_size: int = 14,
        with_footer: bool = False,
        with_icon: bool = True,
        size: str = "450x450",
        text: Optional[str] = None,
        **kwargs,
    ):
        # Initialize base class with a path to the title within the scenario
        group = scenario_key.split(".")[0] if "." in scenario_key else "info"
        super().__init__(
            parent, title_key=f"{group}.__title__", loc_section="notifications"
        )

        self.scenario = scenario_key
        if text is not None:
            msg = self.get_text(text, **kwargs)
        else:
            msg = self.get_text(f"{scenario_key}.message", **kwargs)

        self.raw_text = msg
        self.footer_text = self.get_text(f"{scenario_key}.footer", **kwargs)

        self.icons = self._init_icons()
        # Automatically use scenario_key as icon_type if not explicitly provided
        self.current_icon = self._load_icon(with_icon=with_icon, window_type=group)

        if size:
            self.geometry(size)

        self.with_footer = with_footer
        self._setup_dialog_ui(text_font, font_size)
        self.refresh_localization(**kwargs)
        print(group)

    def _load_icon(
        self, *, with_icon: bool = False, window_type: str
    ) -> Optional[CTkImage]:
        """Loads and scales the icon for the header section."""
        if not with_icon:
            return None

        raw_path = self.icons.get(window_type)
        if not raw_path:
            return None

        icon_path = Path(raw_path)
        print(icon_path)
        if icon_path.is_file():
            try:
                return CTkImage(
                    light_image=Image.open(icon_path).convert("RGBA"), size=(60, 60)
                )
            except (IOError, SyntaxError) as e:
                logger.error(f"Failed to load icon for '{window_type}' window: {e}")
        return None

    def _init_icons(self) -> Dict[str, str]:
        """Maps icon types to their respective file paths."""

        base_path = Path(BASE_PATH) / "src" / "simple_to_pdf" / "icons"
        print(base_path)
        return {
            "info": str(base_path / "info.png"),
            "error": str(base_path / "error.png"),
            "success": str(base_path / "success.png"),
            "warning": str(base_path / "warning.png"),
        }

    def _setup_dialog_ui(self, font_name: str, font_size: int) -> None:
        """Constructs the UI layout and registers widgets for the localization engine."""

        # Header: Icon and Scenario-based Title
        if self.current_icon:
            self.icon_label = BaseLabel(self.header, text="", image=self.current_icon)
            self.icon_label.pack(side="left", padx=(25, 0), pady=(25, 10))

        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].pack(expand=True, pady=(25, 10))

        # Content: Scrollable text area
        self.txt = BaseTextBox(
            self.content, textbox_type="info", font=(font_name, font_size)
        )
        self.txt.insert("1.0", self.raw_text)
        self.txt.configure(state="disabled")
        self.txt.pack(expand=True, fill="both", padx=15, pady=10)

        # Footer: Scenario-based action button
        self.ui["btn_close"] = PrimaryButton(
            self.footer, text="", command=self._on_close, height=40, width=120
        )
        self.ui["btn_close"].pack(side="right", padx=25, pady=15)
        if self.with_footer:
            self.ui["footer_text"] = BaseLabel(
                self.footer, label_type="subtitle", text=""
            )
            self.ui["footer_text"].pack(side="left", padx=25, pady=15)

    def refresh_localization(self, **kwargs) -> None:
        """Synchronizes UI elements with the current language dictionary."""
        super().refresh_localization()  # Updates window title

        # Update header title from scenario
        if "header_title" in self.ui:
            self.ui["header_title"].configure(
                text=self.get_text(f"{self.scenario}.header")
            )

        # Update button text with fallback to general 'OK'
        if "btn_close" in self.ui:
            btn_text = self.get_text(f"{self.scenario}.btn")
            self.ui["btn_close"].configure(text=btn_text)

        if "footer_text" in self.ui:
            footer_text = self.get_text(f"{self.scenario}.footer_text", **kwargs)
            self.ui["footer_text"].configure(text=footer_text)

    def _on_close(self):
        """Cleanup logic before destroying the widget."""
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()
