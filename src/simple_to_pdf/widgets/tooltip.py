from tkinter import TclError
from typing import Any, ClassVar

import customtkinter as ctk

from simple_to_pdf.widgets.base_widgets import BaseLabel


class ToolTip:
    _active: ClassVar["ToolTip | None"] = None

    SHOW_DELAY_MS: ClassVar[int] = 400
    POLL_INTERVAL_MS: ClassVar[int] = 80

    def __init__(self, widget: Any, text: str) -> None:
        self.widget = widget
        self.text: str = text
        self.tooltip_window: ctk.CTkToplevel | None = None
        self._show_job: str | None = None
        self._poll_job: str | None = None

        self.widget.bind("<Enter>", self._schedule_show, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self.hide, add="+")
        self.widget.bind("<MouseWheel>", self.hide, add="+")
        self.widget.bind("<Button-4>", self.hide, add="+")
        self.widget.bind("<Button-5>", self.hide, add="+")
        self.widget.bind("<Destroy>", self.hide, add="+")

    def _pointer_over_widget(self) -> bool:
        """True, if this widget or its descendant is under the cursor."""
        try:
            px, py = self.widget.winfo_pointerxy()
            target = self.widget.winfo_containing(px, py)
        except (TclError, KeyError):
            return False

        while target is not None:
            if target is self.widget:
                return True
            target = getattr(target, "master", None)
        return False

    def _cancel_jobs(self) -> None:
        for attr in ("_show_job", "_poll_job"):
            job = getattr(self, attr)
            if job is not None:
                try:
                    self.widget.after_cancel(job)
                except (TclError, ValueError):
                    pass
                setattr(self, attr, None)

    def _schedule_show(self, event: Any = None) -> None:
        self._cancel_jobs()
        if not self.text:
            return
        try:
            self._show_job = self.widget.after(self.SHOW_DELAY_MS, self._show)
        except TclError:
            self._show_job = None

    def _show(self) -> None:
        self._show_job = None

        if not self._pointer_over_widget():
            return

        if ToolTip._active is not None and ToolTip._active is not self:
            ToolTip._active._destroy()

        self._destroy_window()

        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

            win = ctk.CTkToplevel(self.widget)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{x}+{y}")
            BaseLabel(win, text=self.text, label_type="content").pack()

            self.tooltip_window = win
            ToolTip._active = self
            self._poll()
        except TclError:
            self._destroy()

    def _poll(self) -> None:
        """Поки тултіп видно — перевіряємо, чи курсор ще над віджетом."""
        self._poll_job = None
        if self.tooltip_window is None:
            return
        if not self._pointer_over_widget():
            self._destroy()
            return
        try:
            self._poll_job = self.widget.after(self.POLL_INTERVAL_MS, self._poll)
        except TclError:
            self._destroy()

    def _on_leave(self, event: Any = None) -> None:
        if self._pointer_over_widget():
            return
        self.hide()

    def hide(self, event: Any = None) -> None:
        self._destroy()

    def _destroy_window(self) -> None:
        win, self.tooltip_window = self.tooltip_window, None
        if win is not None:
            try:
                if win.winfo_exists():
                    win.destroy()
            except TclError:
                pass

    def _destroy(self) -> None:
        self._cancel_jobs()
        self._destroy_window()
        if ToolTip._active is self:
            ToolTip._active = None
