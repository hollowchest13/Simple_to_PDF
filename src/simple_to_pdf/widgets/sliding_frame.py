import customtkinter as ctk
from simple_to_pdf.widgets import BaseFrame, BaseLabel, PrimaryButton


class SlidingFrame(BaseFrame):
    def __init__(self, parent, *, title, width=300):
        super().__init__(parent, frame_type="scr_frame_container", width=0)
        self.target_width = width
        self.is_open = False
        self.pack_propagate(False)
        self.pack(side="right", fill="y")
        self.header = BaseFrame(self, frame_type="header", height=50)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        BaseLabel(self.header, text=title, label_type="title").pack(side="top")
        ctk.CTkButton(
            self.header,
            text="×",
            width=30,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self.close,
        ).pack(side="right", padx=10)
        self.container = BaseFrame(self, frame_type="content")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

    def close(self):
        """Force the panel to close if it is currently open."""
        if self.is_open:
            self.toggle()

    def toggle(self):
        """Toggle the panel visibility with a sliding animation."""
        if self.is_open:
            self._animate_width(target=0)
        else:
            self._animate_width(target=self.target_width)
        self.is_open = not self.is_open

    def _animate_width(self, *, target):
        """Incrementally adjust frame width to create a smooth transition."""
        current_width = self.winfo_width()
        step = 25
        if abs(current_width - target) > step:
            if current_width < target:
                new_width = current_width + step
            else:
                new_width = current_width - step
            self.configure(width=new_width)
            self.after(10, lambda: self._animate_width(target=target))
        else:
            self.configure(width=target)
