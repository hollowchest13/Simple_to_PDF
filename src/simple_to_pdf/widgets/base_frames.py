import tkinter as tk
class BaseFrame(tk.Frame):

    def __init__(self, parent, **kwargs):
        if hasattr(parent, 'theme'):
            self.theme = parent.theme
        else:
            self.theme = {"bg_white": "#ffffff"}
        if 'bg' not in kwargs and 'background' not in kwargs:
            kwargs['bg'] = self.theme.get("bg_white", "#ffffff")
            
        super().__init__(parent, **kwargs)