import functools
import logging
import threading
import tkinter as tk
from typing import Literal

import customtkinter as ctk

from simple_to_pdf.widgets.base_widgets import BaseTextBox

logger = logging.getLogger(__name__)


def clear_text_widget(widget: BaseTextBox) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.configure(state="disabled")


def change_state(
    *, widgets_dict: dict[str, ctk.CTkBaseClass], state: Literal["normal", "disabled"]
) -> None:
    """Universal state switcher for a group of widgets."""

    for name, widget in widgets_dict.items():
        try:
            widget.configure(state=state)
        except (tk.TclError, ValueError, KeyError, AttributeError) as e:
            logger.debug(
                f"Could not set '{state}' for widget '{name}'"
                f"({type(widget).__name__}): {e}"
            )
            # Skip if widget doesn't have a state parameter (e.g., Frame)
            pass


def ui_locker(func):
    """
    Decorator to execute a decorated method in a separate background thread
    to keep the GUI responsive.

    IMPORTANT: The class using this decorator MUST implement:
    1. `toggle_ui(active: bool)`: Method to enable/disable UI widgets (buttons, etc.).
    2. `self.thread_running`: Boolean flag to track the background thread status.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, "thread_running", False):
            return
        if hasattr(self, "stop_event"):
            self.stop_event.clear()

        self.toggle_ui(active=False)  # lock in main thread
        self.thread_running = True

        def run():
            try:
                func(self, *args, **kwargs)  # run in background thread
            finally:
                # unlock in main thread
                self.after(0, lambda: self.toggle_ui(active=True))
                self.thread_running = False

        threading.Thread(target=run, daemon=True).start()

    return wrapper
