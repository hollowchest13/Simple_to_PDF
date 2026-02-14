import tkinter as tk
from typing import Optional
import webbrowser
from simple_to_pdf.core import config
from simple_to_pdf.app_dialog.base_dialog import BaseDialog
from simple_to_pdf.widgets import BaseFrame, PrimaryButton,BadgeLabel

class UpdateDialog(BaseDialog):
    """Notifies the user about a new version."""
    def __init__(self, parent, new_version, changelog):
        super().__init__(parent, title="Update Available")
        
        self.set_header_text("New Update!", f"Version {new_version} is ready")
        
        # Content area
        BadgeLabel(
            self.content, text="What's New:"
        ).pack(anchor="w", pady=(0, 5))

        # Text area for changelog (could be a simple label or ScrolledText)
        change_log_box = BadgeLabel(
            self.content, text=changelog
        )
        change_log_box.pack(fill="x", pady=(0, 20))

        # Action buttons in a horizontal layout
        btn_frame = BaseFrame(self.content, bg="white")
        btn_frame.pack(fill="x", pady=10)

        PrimaryButton(
            btn_frame, text="Download Now", 
            command=self._on_update_click
        ).pack(side="right", padx=5)
        
        PrimaryButton(
            btn_frame, text="Later", command=self.destroy
        ).pack(side="right", padx=5)

    def _on_update_click(self):
        # Logic for starting update
        webbrowser.open_new_tab(config.RELEASES_URL)
        self.destroy()