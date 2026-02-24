from simple_to_pdf.core.config import ThemeKeys
from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton, BaseLabel
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
        BaseLabel(self.content, text=f"Engine: {engine_name}",label_type='badge').pack(pady=(0, 20))
        
        # Main description
        BaseLabel(
            self.content, 
            text="Professional utility for batch PDF processing.\nBuilt for efficiency and speed.",
            label_type="content"
        ).pack(pady=10)

        # Primary action button
        PrimaryButton(
            self.content, 
            text="View Source on GitHub", 
            command=lambda: webbrowser.open("https://github.com/your-repo")
        ).pack(pady=(80,20))