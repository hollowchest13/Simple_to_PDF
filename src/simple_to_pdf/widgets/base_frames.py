import tkinter as tk
from simple_to_pdf.utils.ui_tools import ThemeProviderMixin
from simple_to_pdf.core.config import ThemeKeys

class BaseFrame(tk.Frame,ThemeProviderMixin):
    def __init__(self, parent, **kwargs):
        
        # Set background color ONLY if not explicitly provided
        kwargs.setdefault('bg',self.get_color(ThemeKeys.BG_MAIN))
        
        # Call the super constructor with prepared kwargs
        super().__init__(parent, **kwargs)