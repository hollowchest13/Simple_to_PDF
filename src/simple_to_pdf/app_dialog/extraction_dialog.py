import customtkinter as ctk

class PageSelectionDialog(ctk.CTkToplevel):
    def __init__(self, master, title="Extract Pages"):
        super().__init__(master)

        # Налаштування вікна
        self.title(title)
        self.geometry("400x250")
        self.resizable(False, False)
        
        # Модальність (блокуємо головне вікно)
        self.transient(master)
        self.grab_set()

        self.result = None

        # --- UI СЕКЦІЯ (Чистий CTK) ---
        
        # Головний фрейм-контейнер
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        self.label_title = ctk.CTkLabel(
            self.main_frame, 
            text="Select pages to extract:",
            font=("Arial", 14, "bold")
        )
        self.label_title.pack(pady=(0, 5))

        # Підказка
        hint_text = "Format: 1, 3, 5-10\n(use commas for single pages and dashes for ranges)"
        self.label_hint = ctk.CTkLabel(
            self.main_frame, 
            text=hint_text,
            text_color="gray",
            font=("Arial", 12)
        )
        self.label_hint.pack(pady=(0, 15))

        # Поле вводу
        self.entry = ctk.CTkEntry(self.main_frame, placeholder_text="e.g. 1, 2, 5-8")
        self.entry.pack(fill="x", pady=(0, 20))

        # Кнопка підтвердження
        self.btn_ok = ctk.CTkButton(
            self.main_frame, 
            text="Confirm", 
            command=self._on_ok
        )
        self.btn_ok.pack()

        # Фокус і Enter
        self.entry.focus_set()
        self.bind("<Return>", lambda event: self._on_ok())

    def _on_ok(self):
        self.result = self.entry.get().strip()
        self.destroy()

    def get_input(self):
        """Метод для виклику діалогу та отримання результату"""
        # Примусово оновлюємо вікно, щоб воно не було порожнім
        self.update_idletasks()
        self.update()
        
        # Чекаємо на закриття
        self.wait_window(self)
        return self.result