import customtkinter as ctk
from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from simple_to_pdf.widgets import BaseFrame
from simple_to_pdf.localization.localization_mixin import LocalizationMixin


class BaseDialog(ctk.CTkToplevel, ThemeProviderMixin, LocalizationMixin):
    """
    Base class for all modal dialogs in the application.
    Handles centering, theme consistency, and standard layout.
    """

    def __init__(self, parent, *, loc_section: str):
        super().__init__(parent)

        # Window configuration
        self._title_key="window_title"
        self.ui = {}

        # Modal behavior: focus remains on this window until closed
        self.transient(parent)
        self.after(10, self.grab_set)

        # Initialize UI structure
        self._init_layout()
        self.configure(fg_color=self.get_color(ThemeKeys.BG_MAIN))

        # Center the window relative to the parent
        self._center_window(parent)
        self.init_localization()
        self.loc_section = loc_section
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_layout(self):
        """Creates the structural frames: Header, Content, and Footer."""

        # Header: Light gray background for the title area
        self.header = BaseFrame(self, frame_type="header", height=100)
        self.header.pack(fill="x", side="top")

        # Content: Main white area for text and inputs
        self.content = BaseFrame(self, frame_type="content")
        self.content.pack(fill="both", expand=True, padx=35, pady=20)

        # Footer: Bottom area for secondary labels or small buttons
        self.footer = BaseFrame(self, frame_type="footer")
        self.footer.pack(side="bottom", fill="x", pady=15)

    def _center_window(self, parent):
        """Calculates coordinates to center this dialog over the parent window."""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _on_close(self):
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()
    
    def refresh_localization(self) -> None:
        super().refresh_localization()
        if hasattr(self, "_title_key"):
            translated_title = self.get_text(self._title_key)
            self.title(translated_title)
    
