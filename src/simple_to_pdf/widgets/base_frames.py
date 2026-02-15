import tkinter as tk
from simple_to_pdf.core.config import ThemeKeys,DEFAULT_COLORS

class BaseFrame(tk.Frame):
    def __init__(self, parent, **kwargs):

        # Inherit theme from parent or use default
        self.theme = getattr(parent, 'theme', DEFAULT_COLORS)
        
        # Set background color ONLY if not explicitly provided
        kwargs.setdefault('bg', self.theme.get(ThemeKeys.BG_COLOR, "#ffffff"))
        
        # Call the super constructor with prepared kwargs
        super().__init__(parent, **kwargs)