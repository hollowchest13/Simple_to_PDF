import logging
from pathlib import Path
from typing import Callable, List

import customtkinter as ctk
from PIL import Image

from simple_to_pdf.core.config import ICONS_PATH, ThemeKeys
from simple_to_pdf.utils.file_tools import get_file_category
from simple_to_pdf.widgets import BaseFrame, BaseLabel
from simple_to_pdf.widgets.base_widgets import BaseScrollableFrame

logger = logging.getLogger(__name__)


class CTkListbox(BaseScrollableFrame):
    """Scrollable file list widget with row selection and ordering controls."""

    def __init__(self, parent, **kwargs):
        """Initialize the listbox and its internal state containers."""
       
        super().__init__(parent,scr_frame_type="file_list",**kwargs)

        self._scroll_target = 0
        self._is_scrolling = False

        self.all_rows: List[Path] = []
        self.selected_data = {}
        self.all_widgets = {}
        self._icon_cache = {}
        self._icon_size = (24, 24)

        self.default_text_color = self.get_color(ThemeKeys.TEXT_CONTENT)
        self.selected_row_color = self.get_color(ThemeKeys.TEXT_PRIMARY)
        self.selected_text_color = self.get_color(ThemeKeys.TEXT_ON_ACCENT)

    def add_new_files(self, file_list: list[str]) -> None:
        """Append new file paths to the list and refresh the rendered rows."""
        new_paths = [Path(p) for p in file_list]

        existing = set(self.all_rows)

        for path in new_paths:
            if path not in existing:
                self.all_rows.append(path)
                existing.add(path)
        self._update_listbox()

    def _update_listbox(self):
        """Synchronize the rendered widget rows with the current data model."""
        for registered_path in list(self.all_widgets.keys()):
            if registered_path not in self.all_rows:
                widget_data = self.all_widgets.pop(registered_path)
                widget_data["frame"].destroy()

        for path in self.all_rows:
            if path not in self.all_widgets:
                self._create_file_row(file_path=path)

            frame = self.all_widgets[path]["frame"]
            frame.pack_forget()
            frame.pack(fill="x", padx=5, pady=2)

    def _get_file_icon(self, *, file_path: Path):
        """Return the icon widget for a file path, falling back gracefully."""
        file_category = get_file_category(file_path=file_path)

        icon_map = {
            "pdf": "pdf_icon.png",
            "table": "table_icon.png",
            "document": "doc_icon.png",
            "presentation": "pres_icon.png",
            "image": "image_icon.png",
        }
        icon_file = icon_map.get(str(file_category), "default_icon.png")
        try:
            img_path = ICONS_PATH / icon_file
            pil_image = Image.open(img_path)
            ctk_image = ctk.CTkImage(
                light_image=pil_image, dark_image=pil_image, size=self._icon_size
            )
            self._icon_cache[file_category] = ctk_image
            return ctk_image
        except OSError as exc:
            logger.warning("Failed to load icon for %s: %s", file_path, exc)
            return None

    def _create_file_row(self, file_path: Path):
        """Create and register the widgets for a single file row."""
        row = BaseFrame(self, frame_type="list_item", border_width=1)

        icon_image = self._get_file_icon(file_path=file_path)
        icon_label = BaseLabel(row, image=icon_image, text="", label_type="content")
        icon_label.pack(side="left", padx=(10, 5), pady=5)

        path_label = BaseLabel(
            row, text=str(file_path), label_type="content", anchor="w", justify="left"
        )
        path_label.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=5)

        self.all_widgets[file_path] = {
            "frame": row,
            "label": path_label,
            "icon": icon_label,
        }

        for widget in [row, path_label, icon_label]:
            self._bind_mouse_wheel(widget)
            widget.bind("<Button-1>", lambda event, p=file_path: self._select_row(p))

    def _select_row(self, file_path: Path):
        """Toggle the selection state of the row associated with a file path."""
        widgets = self.all_widgets[file_path]
        row_frame = widgets["frame"]
        path_label = widgets["label"]

        if file_path in self.selected_data:
            row_frame.configure(fg_color="transparent")
            path_label.configure(text_color=self.default_text_color)
            self.selected_data.pop(file_path)
        else:
            row_frame.configure(fg_color=self.selected_row_color)
            path_label.configure(text_color=self.selected_text_color)
            self.selected_data[file_path] = widgets

    def _curselection(self) -> tuple[int, ...]:
        """Return the indices of all currently selected rows."""
        return tuple(
            idx for idx, path in enumerate(self.all_rows) if path in self.selected_data
        )

    def move(self, *, direction: str, callback):
        """Move the selected rows up or down and refresh the display."""
        sel_idxs = sorted(self._curselection())
        if not sel_idxs:
            return

        items = self.all_rows
        n = len(items)

        if direction == "down":
            if sel_idxs[-1] < n - 1:
                for i in reversed(sel_idxs):
                    items[i], items[i + 1] = items[i + 1], items[i]

        elif direction == "up":
            if sel_idxs[0] > 0:
                for i in sel_idxs:
                    items[i], items[i - 1] = items[i - 1], items[i]

        self._update_listbox()

        if callback:
            callback()

    def clear(self, *, callback: Callable):
        """Destroy all list rows and reset the list state."""
        for widgets in self.all_widgets.values():
            widgets["frame"].destroy()
        self.all_widgets.clear()
        self.selected_data.clear()
        self.all_rows.clear()
        callback()

    def clear_selection(self):
        """Clear the current selection and restore the default row styling."""
        for widgets in self.selected_data.values():
            widgets["frame"].configure(fg_color="transparent")
            widgets["label"].configure(text_color=self.default_text_color)
        self.selected_data.clear()

    def remove_selected(self, *, callback: Callable):
        """Remove all currently selected files from the list and refresh it."""
        for path in self.selected_data.keys():
            self.all_rows.remove(path)
        self.selected_data.clear()
        self._update_listbox()

    def get_selected_paths(self) -> list[Path]:
        """Return the paths of all currently selected entries."""
        return list(self.selected_data.keys())

    def _bind_mouse_wheel(self, widget):
        """Bind mouse wheel events for smooth scrolling on a child widget."""
        widget.bind("<MouseWheel>", self._handle_mouse_wheel)
        widget.bind("<Button-4>", self._handle_mouse_wheel)
        widget.bind("<Button-5>", self._handle_mouse_wheel)

    def _smooth_scroll_engine(self):
        """Animate the scrollbar movement toward the current scroll target."""
        if abs(self._scroll_target) > 0.001:
            region = self._parent_canvas.cget("scrollregion")
            if not region:
                return

            total_height = float(region.split()[-1])
            if total_height <= 0:
                return

            shift_fraction = (self._scroll_target * 0.2) / total_height
            current_pos = self._parent_canvas.yview()[0]
            new_pos = current_pos + shift_fraction
            new_pos = max(0.0, min(1.0, new_pos))

            self._parent_canvas.yview_moveto(new_pos)
            self._scroll_target -= self._scroll_target * 0.2
            self.after(10, self._smooth_scroll_engine)
        else:
            self._scroll_target = 0
            self._is_scrolling = False

    def _handle_mouse_wheel(self, event):
        """Capture wheel input and start the smooth scrolling animation."""
        if event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            delta = -50
        else:
            delta = 50

        self._scroll_target += delta

        if not self._is_scrolling:
            self._is_scrolling = True
            self._smooth_scroll_engine()
