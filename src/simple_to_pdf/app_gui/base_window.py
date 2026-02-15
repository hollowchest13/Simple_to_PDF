import tkinter as tk

from simple_to_pdf.widgets import BaseFrame
from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.utils.ui_tools import ThemeProvider

class BaseWindow(tk.Tk,ThemeProvider):
    """
    Base class for the main application window.
    Focuses on layout structure and consistent theming.
    """
    
    def __init__(self, **kwargs):
        window_title = kwargs.pop('title', "Window")
        window_size = kwargs.pop('size', "1000x600")

        super().__init__(**kwargs)
        
        self.title(window_title)
        self.geometry(window_size)
        self.configure(background=self.get_color(ThemeKeys.BG_MAIN))
        
        self._init_base_layout()

    def _init_base_layout(self):

        """Creates top-level structural containers for the main window."""
        
        self.root_container=BaseFrame(self)
        self.root_container.pack(fill="both",expand=True)

    def set_window_icon(self, icon_path):
        """Standard way to set icon for the main window."""
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass
