import functools
import logging
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

logger = logging.getLogger(__name__)


def get_text(*, file_name: str, file_path: str) -> str:
    if not os.path.exists(file_path):
        messagebox.showwarning("Warning", f"{file_name} file not found")
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        err_msg = f"Failed to read {file_name}: {e}"
        logger.error(err_msg, exc_info=True)
        messagebox.showerror("Error", err_msg)
        return


def get_files(*, filetypes: list | tuple = (".pdf",), multiple=True):
    """
    Open dialog window to select files.
    Supports both raw extensions: (".pdf", ".docx")
    and ready-made filters: [("Label", "*.ext"), ...]
    """

    # Check if filetypes is already in (label, pattern) format
    if (
        isinstance(filetypes, list)
        and len(filetypes) > 0
        and isinstance(filetypes[0], tuple)
    ):
        filters = filetypes
    else:
        # Logic for raw extensions
        all_supported_mask = " ".join([f"*{ext}" for ext in filetypes])
        filters = [("All supported types", all_supported_mask)]

        for ext in filetypes:
            if isinstance(ext, str):
                filters.append((f"{ext.upper()} files", f"*{ext}"))
    if multiple:
        return filedialog.askopenfilenames(filetypes=filters)

    # For single selection, it's better to use dynamic filters instead of hardcoded PDF
    return filedialog.askopenfilename(filetypes=filters)


def get_pages(*, raw: str) -> list[int] | None:
    pages: list[int] = []
    try:
        for part in raw.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages.extend(range(start - 1, end))  # Convert to 0-based index
            else:
                pages.append(int(part) - 1)  # Convert to 0-based index
        return pages
    except ValueError:
        return None


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
