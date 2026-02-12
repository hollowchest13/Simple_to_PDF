import tkinter as tk

class BaseDialog(tk.Toplevel):
    """
    Base class for all modal dialogs in the application.
    Handles centering, theme consistency, and standard layout.
    """
    def __init__(self, parent, title: str, size: str = "440x500"):
        super().__init__(parent)
        
        # Window configuration
        self.title(title)
        self.geometry(size)
        self.resizable(False, False)
        self.configure(bg="#ffffff")
        
        # Modal behavior: focus remains on this window until closed
        self.transient(parent)
        self.grab_set()
        
        # Standardized color palette (Theme)
        self.theme = {
            "bg_white": "#ffffff",
            "bg_gray": "#f1f4f9",      # Used for header background
            "accent": "#3182ce",       # Main brand color (blue)
            "accent_hover": "#2b6cb0", # Darker blue for button hover
            "text_main": "#1a202c",    # Dark slate for headings
            "text_sub": "#718096",     # Muted gray for secondary text
            "border": "#e2e8f0"
        }

        # Initialize UI structure
        self._init_layout()
        
        # Center the window relative to the parent
        self._center_window(parent)

    def _init_layout(self):
        """Creates the structural frames: Header, Content, and Footer."""
        # Header: Light gray background for the title area
        self.header = tk.Frame(self, bg=self.theme["bg_gray"], height=100)
        self.header.pack(fill="x", side="top")
        
        # Content: Main white area for text and inputs
        self.content = tk.Frame(self, bg=self.theme["bg_white"], padx=35, pady=20)
        self.content.pack(fill="both", expand=True)
        
        # Footer: Bottom area for secondary labels or small buttons
        self.footer = tk.Frame(self, bg=self.theme["bg_white"], pady=15)
        self.footer.pack(side="bottom", fill="x")

    def set_header_text(self, title: str, subtitle: str|None = None):
        """Helper to quickly populate the header area with styled labels."""
        tk.Label(
            self.header, text=title, font=("Segoe UI", 16, "bold"),
            bg=self.theme["bg_gray"], fg=self.theme["text_main"]
        ).pack(pady=(25, 2))
        
        if subtitle:
            tk.Label(
                self.header, text=subtitle, font=("Segoe UI", 9),
                bg=self.theme["bg_gray"], fg=self.theme["text_sub"]
            ).pack(pady=(0, 20))

    def _center_window(self, parent):
        """Calculates coordinates to center this dialog over the parent window."""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")