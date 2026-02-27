from typing import Literal
import customtkinter as ctk
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin

class BaseTextBox(ctk.CTkTextbox,ThemeProviderMixin):
    def __init__(self,parent,*,textbox_type:Literal['status_text'],**kwargs):
        params=self.set_textbox_params(textbox_type=textbox_type)
        params.update(kwargs)
        super().__init__(parent,**params)