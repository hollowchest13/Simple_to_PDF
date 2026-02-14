import tkinter as tk

class PrimaryButton(tk.Button):
    """
    A pre-styled button for main actions.
    Uses the application's accent blue color and Segoe UI font.
    """
    def __init__(self, parent, **kwargs):

        params = {
            "text": "Button",
            "bg": "#3182ce",
            "fg": "white",
            "font": ("Segoe UI", 10, "bold"),
            "activebackground": "#2b6cb0",
            "activeforeground": "white",
            "relief": "flat",
            "padx": 20,
            "pady": 8,
            "cursor": "hand2",
            "command": None 
        }
        
        params.update(kwargs)
        super().__init__(parent, **params)