from typing import Any

import customtkinter as ctk

from simple_to_pdf.widgets.base_widgets import BaseLabel


class ToolTip:
    def __init__(self, widget: Any, text: str):
        self.widget = widget
        self.text: str = text
        self.tooltip_window: ctk.CTkToplevel | None = None
        self.bind_recursive(self.widget)

    def bind_recursive(self, widget: Any) -> None:
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        for child in widget.winfo_children():
            self.bind_recursive(child)

    def show(self, event: Any = None) -> None:
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = BaseLabel(
            self.tooltip_window,
            text=self.text,
            corner_radius=4,
            fg_color=("gray85", "gray20"),
            text_color=("black", "white"),
            padx=8,
            pady=4,
            font=("Arial", 11),
        )
        label.pack()

    def hide(self, event: Any = None) -> None:
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
