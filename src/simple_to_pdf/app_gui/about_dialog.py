import tkinter as tk
import webbrowser
from datetime import datetime
from simple_to_pdf.core import config

class AboutDialog(tk.Toplevel):
    def __init__(self, parent, version, engine_name):
        super().__init__(parent)
        
        # Налаштування вікна
        self.title(f"About {config.APP_NAME}")
        self.geometry("420x460")
        self.resizable(False, False)
        self.configure(bg="#ffffff") # Білий фон як база
        
        # Модальність
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui(version, engine_name)
        self._center_window(parent)

    def _setup_ui(self, version, engine_name):
        # 1. Header (Світло-сірий фон, як в інших вікнах)
        header = tk.Frame(self, bg="#f8f9fa", height=100)
        header.pack(fill="x", side="top")
        
        tk.Label(
            header, text=config.APP_NAME,
            font=("Segoe UI", 16, "bold"), bg="#f8f9fa", fg="#2c3e50"
        ).pack(pady=(25, 2))
        
        tk.Label(
            header, text=f"Version {version}",
            font=("Segoe UI", 10), bg="#f8f9fa", fg="#7f8c8d"
        ).pack(pady=(0, 20))

        # 2. Main Content
        content = tk.Frame(self, bg="#ffffff", padx=40, pady=20)
        content.pack(fill="both", expand=True)

        # Engine Info (Блакитний акцент)
        tk.Label(
            content, text=f"ENGINE: {engine_name.upper()}",
            font=("Consolas", 9, "bold"), bg="#ebf5fb", fg="#3498db", # Тепер блакитний!
            padx=10, pady=3
        ).pack(pady=(0, 15))

        # Description
        tk.Label(
            content, 
            text="Professional tool for batch conversion\nand merging documents into PDF.",
            bg="#ffffff", font=("Segoe UI", 10), fg="#34495e", justify="center"
        ).pack(pady=10)

        # GitHub Button (Використовуємо той самий Блакитний #3498db)
        github_btn = tk.Button(
            content, text="View on GitHub",
            bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", padx=30, pady=8, cursor="hand2",
            activebackground="#2980b9", # Темніший при натисканні
            command=lambda: webbrowser.open(config.GITHUB_REPO_URL)
        )
        github_btn.pack(pady=20)

        # 3. Footer
        footer_text = f"© {datetime.now().year} All Rights Reserved"
        tk.Label(
            self, text=footer_text,
            font=("Segoe UI", 8), bg="#ffffff", fg="#bdc3c7"
        ).pack(side="bottom", pady=15)

    def _center_window(self, parent):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")