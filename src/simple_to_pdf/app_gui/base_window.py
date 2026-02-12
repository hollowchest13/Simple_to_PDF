import tkinter as tk

from simple_to_pdf.widgets.widgets import BaseFrame

class BaseWindow(tk.Tk):
    """
    Base class for the main application window.
    Focuses on layout structure and consistent theming.
    """
    def __init__(self,*, title:str,size:str="1000x650"):
        super().__init__()
        self.theme={
            "bg_white": "#ffffff",
            "bg_gray": "#f8f9fa",
            "accent": "#3498db",
            "text_main": "#2c3e50",
            "border": "#e2e8f0"
        }
        self.title(title)
        self.geometry(size)
        self.configure(bg=self.theme['bg_white'])
        self._init_base_layout()
    
    def _init_base_layout(self):
        """Creates top-level structural containers for the main window."""
        self.root_container=BaseFrame(self,bg=self.theme["bg_white"])
        self.root_container.pack(fill="both",expand=True)

    def set_window_icon(self, icon_path):
        """Standard way to set icon for the main window."""
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass
