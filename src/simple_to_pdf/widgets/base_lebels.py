import tkinter as tk
from simple_to_pdf.utils.ui_tools import ThemeProviderMixin
from simple_to_pdf.core.config import ThemeKeys

class BadgeLabel(tk.Label,ThemeProviderMixin):
    """
    A label styled as a 'badge' or 'chip'.
    Ideal for displaying versions, engine names, or status tags.
    """
   
    def __init__(self, parent, **kwargs):

        bg_color=self.get_color(ThemeKeys.BG_MAIN)
        fg_color=self.get_color(ThemeKeys.ACCENT)

        params = {
            "text": "Default",
            "font": ("Consolas", 9, "bold"),
            "bg": bg_color,
            "fg": fg_color,
            "padx": 10,
            "pady": 4,
            "relief": "flat"
        }
        params.update(kwargs)
        
        super().__init__(parent, **params)

class SectionTitle(tk.Label,ThemeProviderMixin):
    """
    Standardized title for content sections.
    """
    def __init__(self, parent, **kwargs):

        bg_color=self.get_color(ThemeKeys.BG_MAIN)
        fg_color=self.get_color(ThemeKeys.TEXT_PRIMARY)

        params = {
            "text": "Section Title",
            "font": ("Segoe UI", 11, "bold"),
            "bg": bg_color,
            "fg": fg_color,
            "anchor": "w",      
            "pady": 5
        }

        params.update(kwargs)
        
        super().__init__(parent, **params)