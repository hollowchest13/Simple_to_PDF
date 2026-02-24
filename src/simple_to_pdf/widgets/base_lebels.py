import tkinter as tk
from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from typing import Literal

class BaseLabel(tk.Label,ThemeProviderMixin):
    """
    A label styled as a 'badge' or 'chip'.
    Ideal for displaying versions, engine names, or status tags.
    """
    def __init__(self, parent,*,label_type:Literal['badge','title','content']='badge', **kwargs):
        params = self.set_label_params(parent=parent,label_type=label_type)
        params.update(kwargs)
        super().__init__(parent, **params)
