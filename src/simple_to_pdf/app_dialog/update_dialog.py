import tkinter as tk
import webbrowser

from simple_to_pdf.app_dialog.base_dialog import BaseDialog
from simple_to_pdf.widgets.widgets import PrimaryButton

class UpdateDialog(BaseDialog):
    """Notifies the user about a new version."""
    def __init__(self, parent, new_version, changelog):
        super().__init__(parent, title="Update Available", size="460x520")
        
        self.set_header_text("New Update!", f"Version {new_version} is ready")
        
        # Content area
        tk.Label(
            self.content, text="What's New:", 
            font=("Segoe UI", 10, "bold"), bg="white", fg="#1a202c"
        ).pack(anchor="w", pady=(0, 5))

        # Text area for changelog (could be a simple label or ScrolledText)
        change_log_box = tk.Label(
            self.content, text=changelog, 
            bg="#f8f9fa", fg="#4a5568", font=("Consolas", 9),
            padx=15, pady=15, justify="left", wraplength=380
        )
        change_log_box.pack(fill="x", pady=(0, 20))

        # Action buttons in a horizontal layout
        btn_frame = tk.Frame(self.content, bg="white")
        btn_frame.pack(fill="x", pady=10)

        PrimaryButton(
            btn_frame, text="Download Now", 
            command=self._on_update_click
        ).pack(side="right", padx=5)
        
        tk.Button(
            btn_frame, text="Later", command=self.destroy,
            relief="flat", bg="white", fg="#718096", cursor="hand2"
        ).pack(side="right", padx=5)

    def _on_update_click(self):
        # Logic for starting update
        print("Starting update process...")
        self.destroy()