import tkinter as tk

class PrimaryButton(tk.Button):
    """
    A pre-styled button for main actions.
    Includes a hover effect that changes the background color.
    """
    def __init__(self, parent, **kwargs):
        # 1. Define default colors
        self.default_bg = "#3182ce"
        
        # Extract hover_bg if provided, otherwise use default light blue
        self.hover_bg = str(kwargs.pop("hover_bg", "#4299e1"))
        
        params = {
            "text": "Button",
            "bg": self.default_bg,
            "fg": "white",
            "font": ("Segoe UI", 10, "bold"),
            "activebackground": "#2b6cb0",
            "activeforeground": "white",
            "relief": "flat",
            "padx": 2,
            "pady": 2,
            "cursor": "hand2",
            "command": None
        }

        # 2. Update default params with user-provided kwargs
        params.update(kwargs)
        
        # 3. Store the final background color for the hover logic
        self.default_bg = str(params["bg"])

        # 4. Initialize the base tk.Button class
        super().__init__(parent, **params)

        # 5. Bind mouse events for hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Change background color when mouse enters the button area."""
        self.configure(background=self.hover_bg)

    def _on_leave(self, event):
        """Restore original background color when mouse leaves the button area."""
        self.configure(background=self.default_bg)