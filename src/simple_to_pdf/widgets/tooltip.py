from tkinter import TclError
from typing import Any

import customtkinter as ctk

from simple_to_pdf.widgets.base_widgets import BaseLabel


class ToolTip:
    def __init__(self, widget: Any, text: str) -> None:
        self.widget = widget
        self.text: str = text
        self.tooltip_window: ctk.CTkToplevel | None = None
        self.widget.bind("<Enter>", self.show, add="+")
        self.widget.bind("<Leave>", self.hide, add="+")

    def show(self, event: Any = None) -> None:
        if not self.text or self.tooltip_window:
            return

        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

            self.tooltip_window = ctk.CTkToplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

            label = BaseLabel(self.tooltip_window, text=self.text, label_type="content")
            label.pack()
        except TclError:
            self._destroy_window()

    def hide(self, event: Any = None) -> None:
        if not self.tooltip_window:
            return

        try:
            pointer_x = self.widget.winfo_pointerx()
            pointer_y = self.widget.winfo_pointery()
            wx = self.widget.winfo_rootx()
            wy = self.widget.winfo_rooty()
            ww = self.widget.winfo_width()
            wh = self.widget.winfo_height()

            margin_y = 4

            if (wx <= pointer_x <= wx + ww) and (
                wy + margin_y <= pointer_y <= wy + wh - margin_y
            ):
                return

        except TclError:
            pass
        self._destroy_window()

    def _destroy_window(self) -> None:
        if self.tooltip_window:
            try:
                if self.tooltip_window.winfo_exists():
                    self.tooltip_window.destroy()
            except TclError:
                pass
            self.tooltip_window = None
