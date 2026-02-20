import tkinter as tk
from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.utils.ui_tools import ThemeProviderMixin

class BaseDialog(tk.Toplevel,ThemeProviderMixin):
    """
    Base class for all modal dialogs in the application.
    Handles centering, theme consistency, and standard layout.
    """
    def __init__(self, parent, title: str):
        super().__init__(parent)
        
        # Window configuration
        self.title(title)
        self.configure(bg=self.get_color(ThemeKeys.BG_MAIN))
        
        # Modal behavior: focus remains on this window until closed
        self.transient(parent)
        self.grab_set()

        # Initialize UI structure
        self._init_layout()
        
        # Center the window relative to the parent
        self._center_window(parent)

    def _init_layout(self):
        """Creates the structural frames: Header, Content, and Footer."""
        # Header: Light gray background for the title area
        self.header = tk.Frame(self, bg=self.get_color(ThemeKeys.BG_HEADER), height=100)
        self.header.pack(fill="x", side="top")
        
        # Content: Main white area for text and inputs
        self.content = tk.Frame(self, bg=self.get_color(ThemeKeys.BG_MAIN), padx=35, pady=20)
        self.content.pack(fill="both", expand=True)
        
        # Footer: Bottom area for secondary labels or small buttons
        self.footer = tk.Frame(self, bg=self.get_color(ThemeKeys.BG_MAIN), pady=15)
        self.footer.pack(side="bottom", fill="x")

    def set_header_text(self, title: str, subtitle: str|None = None):
        """Helper to quickly populate the header area with styled labels."""
        tk.Label(
            self.header, text=title, font=("Segoe UI", 16, "bold"),
            bg=self.get_color(ThemeKeys.BG_HEADER), fg=self.get_color(ThemeKeys.TEXT_SECONDARY)
        ).pack(pady=(25, 2))
        
        if subtitle:
            tk.Label(
                self.header, text=subtitle, font=("Segoe UI", 9),
                bg=self.get_color(ThemeKeys.BG_HEADER), fg=self.get_color(ThemeKeys.TEXT_SECONDARY)
            ).pack(pady=(0, 20))

    def _center_window(self, parent):
        """Calculates coordinates to center this dialog over the parent window."""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")