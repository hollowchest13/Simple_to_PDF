import tkinter as tk
from tkinter import scrolledtext

class InfoDialog(tk.Toplevel):
    def __init__(
        self, 
        parent, 
        text: str, 
        title: str, 
        header_title: str = "Information",
        size: str = "700x550", 
        text_font: str = "Segoe UI", 
        font_size: int = 10
    ):
        super().__init__(parent)
        
        # Window Setup
        self.title(title)
        self.geometry(size)
        self.configure(bg="#ffffff")
        self.transient(parent)
        self.grab_set()
        
        # UI Construction
        self._build_ui(text, header_title, text_font, font_size)
        self._center_window(parent)

    def _build_ui(self, text, header_title, text_font, font_size):
        # 1. Header Section
        header_frame = tk.Frame(self, bg="#f8f9fa", height=65)
        header_frame.pack(fill="x", side="top")
        
        tk.Label(
            header_frame, 
            text=header_title,
            font=("Segoe UI", 12, "bold"), 
            bg="#f8f9fa", 
            fg="#2c3e50"
        ).pack(pady=18, padx=25, anchor="w")

        # 2. Content Area
        content_frame = tk.Frame(self, bg="#ffffff", padx=20, pady=10)
        content_frame.pack(fill="both", expand=True)

        self.txt = scrolledtext.ScrolledText(
            content_frame, 
            wrap=tk.WORD, 
            font=(text_font, font_size),
            bg="#ffffff",
            fg="#34495e",
            relief="flat",
            padx=10,
            pady=10
        )
        self.txt.insert(tk.END, text)
        self.txt.config(state=tk.DISABLED)
        self.txt.pack(expand=True, fill="both")

        # 3. Footer Section
        footer = tk.Frame(self, bg="#ffffff", pady=15)
        footer.pack(side="bottom", fill="x")

        # Stylish "Got it!" button
        btn_close = tk.Button(
            footer, 
            text="Got it!", 
            command=self.destroy,
            bg="#3498db", 
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=30,
            pady=6,
            cursor="hand2",
            activebackground="#2980b9",
            activeforeground="white"
        )
        btn_close.pack(side="right", padx=25)

    def _center_window(self, parent):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")