import functools
import logging
import threading
import tkinter as tk

logger = logging.getLogger(__name__)


def clear_text_widget(widget: tk.Text) -> None:
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.config(state="disabled")


def get_selected_values(*, listbox: tk.Listbox) -> list[str]:
    selection = listbox.curselection()
    if not selection:
        return []
    return [(listbox.get(i)) for i in listbox.curselection()]


# List Updating
def list_update(*, files: list[str], listbox: tk.Listbox) -> None:
    listbox_clear(listbox=listbox)
    for pdf in files:
        listbox.insert(tk.END, pdf)


def listbox_clear(*, listbox: tk.Listbox) -> None:
    listbox.delete(0, tk.END)


# Reselect items after update
def reselect_items(*, all_items: list, selected_values: list, listbox: tk.Listbox):
    listbox.selection_clear(0, tk.END)
    for idx, val in enumerate(all_items):
        if val in selected_values:
            listbox.selection_set(idx)


def change_state(*, widgets_dict: dict[str, tk.Widget], state: str) -> None:
    """Universal state switcher for a group of widgets."""

    for widget in widgets_dict.values():
        try:
            widget.config(state=state)
        except tk.TclError:
            # Skip if widget doesn't have a state parameter (e.g., Frame)
            pass


def ui_locker(func):
    """
    Decorator to execute a method in a background thread.

    IMPORTANT: The class using this decorator MUST implement a
    `toggle_ui(active: bool)` method to manage widget states.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        self.toggle_ui(active=False)  # lock in main thread

        def run():
            try:
                func(self, *args, **kwargs)  # run in background thread
            finally:
                # unlock in main thread
                self.after(0, lambda: self.toggle_ui(active=True))

        threading.Thread(target=run, daemon=True).start()

    return wrapper
