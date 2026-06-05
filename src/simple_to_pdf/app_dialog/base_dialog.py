import logging
from pathlib import Path
from typing import Dict, Optional

import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image

from simple_to_pdf.core.config import ROOT_PATH, ThemeKeys
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from simple_to_pdf.widgets import BaseFrame

logger = logging.getLogger(__name__)


class BaseDialog(ctk.CTkToplevel, ThemeProviderMixin, LocalizationMixin):
    """
    Base class for all modal dialogs in the application.
    Handles centering, theme consistency, and standard layout.
    """

    def __init__(self, parent, *, title_key="window_title", loc_section: str):
        super().__init__(parent)

        """
        Setup base window configuration
        """
        self._title_key = title_key
        self.ui = {}

        self.resizable(False, False)
        self.transient(parent)

        self._init_layout()
        self.icons = self._init_icons()
        self.configure(fg_color=self.get_color(ThemeKeys.BG_MAIN))
        self.init_localization()
        self.loc_section = loc_section
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._center_window(parent)

        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    def _init_layout(self):
        """Creates the structural frames: Header, Content, and Footer."""

        self.header = BaseFrame(self, frame_type="header", height=100)
        self.header.pack(fill="x", side="top")

        self.content = BaseFrame(self, frame_type="content")
        self.content.pack(fill="both", expand=True, padx=25, pady=20)

        self.footer = BaseFrame(self, frame_type="footer")
        self.footer.pack(side="bottom", fill="x", pady=15)

    def _center_window(self, parent):
        """
        Calculates coordinates to center this dialog over the parent window.
        """
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _on_close(self):
        """
        Unregister from observers and destroy the dialog.
        """
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()

    def refresh_localization(self) -> None:
        """
        Refresh the dialog's localized UI elements and window title.

        Calls the base class implementation to update general UI components,
        then checks for and applies the translated window title if a
        title key has been defined.
        """
        super().refresh_localization()
        if hasattr(self, "_title_key"):
            translated_title = self.get_text(self._title_key)
            self.title(translated_title)

    def _init_icons(self) -> Dict[str, str]:
        """
        Maps icon types to their respective file paths.
        """

        base_path = ROOT_PATH / "icons"

        return {
            "info": str(base_path / "info.png"),
            "error": str(base_path / "error.png"),
            "success": str(base_path / "success.png"),
            "warning": str(base_path / "warning.png"),
            "confirmation": str(base_path / "confirmation.png"),
        }

    def _load_icon(
        self, *, with_icon: bool = False, window_type: str
    ) -> Optional[CTkImage]:
        """
        Loads and scales the icon for the header section.
        """
        if not with_icon:
            return None

        raw_path = self.icons.get(window_type)
        if not raw_path:
            return None

        icon_path = Path(raw_path)
        if icon_path.is_file():
            try:
                return CTkImage(
                    light_image=Image.open(icon_path).convert("RGBA"), size=(60, 60)
                )
            except (IOError, SyntaxError) as e:
                logger.error(f"Failed to load icon for '{window_type}' window: {e}")
        return None
