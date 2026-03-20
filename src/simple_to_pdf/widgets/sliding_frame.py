import customtkinter as ctk
from simple_to_pdf.widgets import (
    BaseFrame,
    BaseLabel,
    PrimaryButton,
    BaseScrollableFrame,
)


class SlidingFrame(BaseFrame):
    def __init__(self, parent, *, title, open_width: int = 200, closed_width: int = 0):
        super().__init__(parent, frame_type="scr_frame_container", width=closed_width)
        self.open_width = open_width
        self.closed_width = closed_width
        self.is_open = False
        self.pack_propagate(False)
        self.container = BaseFrame(self, frame_type="content")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle(self):
        """Toggle the panel visibility with a sliding animation."""
        if self.is_open:
            self._animate_width(target=self.closed_width)
        else:
            self._animate_width(target=self.open_width)
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
