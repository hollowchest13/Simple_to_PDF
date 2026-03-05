import customtkinter as ctk
from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from simple_to_pdf.widgets import BaseFrame, BaseLabel


class BaseDialog(ctk.CTkToplevel, ThemeProviderMixin):
    """
    Base class for all modal dialogs in the application.
    Handles centering, theme consistency, and standard layout.
    """

    def __init__(self, parent, title: str):
        super().__init__(parent)

        # Window configuration
        self.title(title)

        # Modal behavior: focus remains on this window until closed
        self.transient(parent)
        self.after(10, self.grab_set)

        # Initialize UI structure
        self._init_layout()
        self.configure(fg_color=self.get_color(ThemeKeys.BG_MAIN))

        # Center the window relative to the parent
        self._center_window(parent)

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

    def set_header_text(self, title: str, subtitle: str | None = None):
        """Helper to quickly populate the header area with styled labels."""
        BaseLabel(self.header, text=title, label_type="title").pack(pady=(25, 2))

        if subtitle:
            BaseLabel(self.header, text=subtitle, label_type="subtitle").pack(pady=(0, 20))

    def _center_window(self, parent):
        """Calculates coordinates to center this dialog over the parent window."""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
