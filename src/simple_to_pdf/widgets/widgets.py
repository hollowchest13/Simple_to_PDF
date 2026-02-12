import tkinter as tk

class PrimaryButton(tk.Button):
    """
    A pre-styled button for main actions.
    Uses the application's accent blue color and Segoe UI font.
    """
    def __init__(self, master, text, command=lambda: None, **kwargs):
        # Default styling for the primary button
        theme = {
            "bg": "#3182ce",
            "fg": "white",
            "font": ("Segoe UI", 10, "bold"),
            "active_bg": "#2b6cb0"
        }
        
        super().__init__(
            master, 
            text=text, 
            command=command,
            bg=theme["bg"],
            fg=theme["fg"],
            font=theme["font"],
            activebackground=theme["active_bg"],
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            **kwargs
        )

class BadgeLabel(tk.Label):
    """
    A label styled as a 'badge' or 'chip'.
    Ideal for displaying versions, engine names, or status tags.
    """
    def __init__(self, master, text, **kwargs):
        super().__init__(
            master,
            text=text.upper(),
            font=("Consolas", 9, "bold"),
            bg="#ebf5fb",  # Light blue tint
            fg="#3182ce",  # Main accent blue
            padx=10,
            pady=4,
            **kwargs
        )

class SectionTitle(tk.Label):
    """
    Standardized title for content sections.
    """
    def __init__(self, master, text, **kwargs):
        super().__init__(
            master,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#1a202c",
            **kwargs
        )
    
class BaseFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        if hasattr(parent, 'theme'):
            self.theme = parent.theme
        else:
            self.theme = {"bg_white": "#ffffff"}
        self.configure(bg=self.theme["bg_white"])