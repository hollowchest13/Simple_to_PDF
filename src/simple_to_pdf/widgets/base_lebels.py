import tkinter as tk
class BadgeLabel(tk.Label):
    """
    A label styled as a 'badge' or 'chip'.
    Ideal for displaying versions, engine names, or status tags.
    """
   
    def __init__(self, parent, **kwargs):

        params = {
            "text": "Default",
            "font": ("Consolas", 9, "bold"),
            "bg": "#ebf5fb",
            "fg": "#3182ce",
            "padx": 10,
            "pady": 4,
            "relief": "flat"
        }
        params.update(kwargs)
        params["text"] = str(params["text"]).upper()
        
        super().__init__(parent, **params)

class SectionTitle(tk.Label):
    """
    Standardized title for content sections.
    """
    def __init__(self, parent, **kwargs):

        params = {
            "text": "Section Title",
            "font": ("Segoe UI", 11, "bold"),
            "bg": "white",
            "fg": "#1a202c",
            "anchor": "w",      
            "pady": 5
        }

        params.update(kwargs)
        
        super().__init__(parent, **params)