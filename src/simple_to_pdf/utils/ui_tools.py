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


def threaded_task(func):
    """
    Decorator to execute a decorated method in a separate background thread
    to keep the GUI responsive.

    IMPORTANT: The class using this decorator MUST implement:
    1. `toggle_ui(active: bool)`: Method to enable/disable UI widgets (buttons, etc.).
    2. `self.thread_running`: Boolean flag to track the background thread status.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, "_clear_ui_queue"):
            self._clear_ui_queue()
        if getattr(self, "thread_running", False):
            return
        if hasattr(self, "_manage_services"):
            self._manage_services(action="reset")
        if hasattr(self, "clear_console"):
            self.clear_console()
        self.toggle_ui(active=False)  # lock in main thread

        def _unlock_ui():
            self.thread_running = False
            self.toggle_ui(active=True)

        def run():
            try:
                self.thread_running = True
                func(self, *args, **kwargs)  # run in background thread
            finally:
                if hasattr(self, "schedule_ui_task"):
                    self.schedule_ui_task(_unlock_ui)
                else:
                    self.after(0, _unlock_ui)

                logger.info(f"Thread {func.__name__} ended work")

        threading.Thread(target=run, daemon=False).start()

    return wrapper
