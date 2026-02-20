import customtkinter as ctk
from simple_to_pdf.utils.ui_tools import ThemeProviderMixin
from simple_to_pdf.core.config import ThemeKeys

class PrimaryButton(ctk.CTkButton,ThemeProviderMixin):
    """
    A pre-styled button for main actions.
    Includes a hover effect that changes the background color.
    """
    def __init__(self, parent, **kwargs):

        default_accent = self.get_color(ThemeKeys.ACCENT)
        hover_accent = self.get_color(ThemeKeys.ACCENT_HOVER)
        text_color = self.get_color(ThemeKeys.TEXT_ON_ACCENT)
        
        params = {
            "text": "Button",
            "fg_color": default_accent,     
            "hover_color": hover_accent,   
            "text_color": text_color,        
            "font": ("Segoe UI", 13, "bold"),
            "corner_radius": 8,              
            "cursor": "hand2",
            "command": None,
        }
        params.update(kwargs)

        super().__init__(parent, **params)

