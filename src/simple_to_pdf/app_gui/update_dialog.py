import tkinter as tk
from tkinter import ttk
import webbrowser
from simple_to_pdf.core import config

class UpdateDialog(tk.Toplevel):
    def __init__(self, parent, release_info):
        super().__init__(parent)
        
        self.title("Software Update")
        self.geometry("480x420")
        self.resizable(False, False)
        self.configure(bg="#ffffff")
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        self.release = release_info
        self._setup_ui()
        
        # Center the window relative to parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        # Header Section
        header = tk.Frame(self, bg="#f8f9fa", height=90)
        header.pack(fill="x", side="top")
        
        tk.Label(
            header, text="🚀 New Version Available!",
            font=("Segoe UI", 14, "bold"), bg="#f8f9fa", fg="#2c3e50"
        ).pack(pady=(25, 5))

        # Main Content
        content = tk.Frame(self, bg="#ffffff", padx=35, pady=20)
        content.pack(fill="both", expand=True)

        # Version & Date Info
        version_str = f"Version {self.release.version} (Released: {self.release.date})"
        tk.Label(
            content, text=version_str,
            font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#7f8c8d"
        ).pack(anchor="w")

        # Changelog / Release Notes
        tk.Label(
            content, text="What's New:",
            font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2c3e50"
        ).pack(anchor="w", pady=(15, 5))

        # Scrollable Text Area for Notes
        notes_frame = tk.Frame(content, bg="#ecf0f1", padx=1, pady=1)
        notes_frame.pack(fill="both", expand=True)

        self.notes_text = tk.Text(
            notes_frame, font=("Segoe UI", 9), bg="#fdfdfd",
            relief="flat", height=7, padx=12, pady=12, wrap="word"
        )
        self.notes_text.insert("1.0", self.release.notes)
        self.notes_text.config(state="disabled") # Read-only
        self.notes_text.pack(fill="both", expand=True)

        # Footer / Buttons
        footer = tk.Frame(self, bg="#ffffff", pady=25)
        footer.pack(side="bottom", fill="x")

        # Primary Action: Download
        btn_download = tk.Button(
            footer, text="Download Now",
            bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", padx=25, pady=8, cursor="hand2",
            command=self._on_download_click
        )
        btn_download.pack(side="right", padx=(15, 35))

        # Secondary Action: Close
        tk.Button(
            footer, text="Remind Me Later",
            bg="#ffffff", fg="#95a5a6", font=("Segoe UI", 10),
            relief="flat", padx=10, cursor="hand2",
            command=self.destroy
        ).pack(side="right")

    def _on_download_click(self):
        """Open the URL and close the dialog."""
        url = getattr(self.release, 'url', config.RELEASES_URL)
        webbrowser.open(url)
        self.destroy()