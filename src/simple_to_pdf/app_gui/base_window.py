import tkinter as tk

from simple_to_pdf.widgets import BaseFrame
from simple_to_pdf.core.config import ThemeKeys,DEFAULT_COLORS
from simple_to_pdf.utils.ui_tools import ThemeProvider

class BaseWindow(tk.Tk,ThemeProvider):
    """
    Base class for the main application window.
    Focuses on layout structure and consistent theming.
    """
    def __init__(self, **kwargs):
        window_title = kwargs.pop('title', "Window")
        window_size = kwargs.pop('size', "1000x600")
        
        temp_theme = DEFAULT_COLORS.copy()
        bg_color = kwargs.pop('bg', temp_theme.get(ThemeKeys.BG_COLOR, "#ffffff"))

        super().__init__(**kwargs)
        
        self.theme = temp_theme
        self.title(window_title)
        self.geometry(window_size)
        self.configure(background=bg_color)
        
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
