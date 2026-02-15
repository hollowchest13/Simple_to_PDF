from simple_to_pdf.core.config import ThemeKeys
from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton, BadgeLabel
import tkinter as tk
import webbrowser

class AboutDialog(BaseDialog):

    """Displays information about the app and engine."""

    def __init__(self, parent, version, engine_name):
        # We call the parent constructor with title and size
        super().__init__(parent, title="About")
        
        # Use our helper from BaseDialog to set the header
        self.set_header_text("Simple to PDF", f"Version {version}")
        
        # Add a badge for the engine name
        BadgeLabel(self.content, text=f"Engine: {engine_name}").pack(pady=(0, 20))
        
        # Main description
        tk.Label(
            self.content, 
            text="Professional utility for batch PDF processing.\nBuilt for efficiency and speed.",
            bg=self.get_color(ThemeKeys.BG_MAIN), font=("Segoe UI", 10), fg=self.get_color(ThemeKeys.TEXT_PRIMARY)
        ).pack(pady=10)

        # Primary action button
        PrimaryButton(
            self.content, 
            text="View Source on GitHub", 
            command=lambda: webbrowser.open("https://github.com/your-repo")
        ).pack(pady=(80,20))