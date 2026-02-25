import customtkinter as ctk
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin

class PrimaryButton(ctk.CTkButton,ThemeProviderMixin):
    """
    A pre-styled button for main actions.
    Includes a hover effect that changes the background color.
    """
    def __init__(self, parent, **kwargs):
        params = self.set_button_params()
        params.update(kwargs)
        super().__init__(parent, **params)