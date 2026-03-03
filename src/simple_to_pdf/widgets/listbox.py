from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.widgets import BaseFrame, BaseLabel
from pathlib import Path
import customtkinter as ctk


class CTkListbox(ctk.CTkScrollableFrame, ThemeProviderMixin):
    def __init__(self, parent, **kwargs):
        params = self.set_scrollable_frame_params(scr_frame_type="file_list")
        params.update(kwargs)
        super().__init__(parent, **params)

        self._scroll_target = 0
        self._is_scrolling = False

        # self.all_rows stores the order of file paths (Path objects)
        self.all_rows = []
        # self.selected_data stores only selected items: {Path: {"frame": ..., "label": ...}}
        self.selected_data = {}
        # self.all_widgets stores ALL created widgets: {Path: {"frame": ..., "label": ...}}
        self.all_widgets = {}

        self.default_text_color = self.get_color(ThemeKeys.TEXT_PRIMARY)
        self.selected_row_color = self.get_color(ThemeKeys.TEXT_PRIMARY)
        self.selected_text_color = self.get_color(ThemeKeys.TEXT_ON_ACCENT)

    def refresh(self, file_list: list):
        """
        Updates the list. If files are new, creates widgets.
        If only the order has changed, repacks existing widgets.
        """
        new_paths = [Path(p) for p in file_list]

        # Remove widgets for files that are no longer in the list
        for old_path in list(self.all_widgets.keys()):
            if old_path not in new_paths:
                self.all_widgets[old_path]["frame"].destroy()
                self.all_widgets.pop(old_path)
                if old_path in self.selected_data:
                    self.selected_data.pop(old_path)

        # Update the main path list
        self.all_rows = new_paths

        # Create widgets for new files and repack all according to the new order
        for path in self.all_rows:
            if path not in self.all_widgets:
                # Create a new row if it doesn't exist yet
                self._create_file_row(file_path=path)

            # Repack the frame at the end of the stack (this updates the visual order)
            frame = self.all_widgets[path]["frame"]
            frame.pack_forget()
            frame.pack(fill="x", padx=5, pady=2)

    def _create_file_row(self, file_path: Path):
        """Creates a widget row and stores it in the all_widgets registry."""
        row = BaseFrame(self, frame_type="list_item", border_width=1)
        path_label = BaseLabel(
            row, text=str(file_path), label_type="content", anchor="w", justify="left"
        )
        path_label.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=5)

        # Save to the global registry
        self.all_widgets[file_path] = {"frame": row, "label": path_label}
        # Register all parts of the row for mouse wheel scrolling
        self._bind_mouse_wheel(row)
        self._bind_mouse_wheel(path_label)

        def on_click(event):
            self._select_row(file_path=file_path)

        row.bind("<Button-1>", on_click)
        path_label.bind("<Button-1>", on_click)

    def _select_row(self, file_path: Path):
        """Manages the selection state of a row."""
        widgets = self.all_widgets[file_path]
        row_frame = widgets["frame"]
        path_label = widgets["label"]

        if file_path in self.selected_data:
            # Deselect the row
            row_frame.configure(fg_color="transparent")
            path_label.configure(text_color=self.default_text_color)
            self.selected_data.pop(file_path)
        else:
            # Select the row
            row_frame.configure(fg_color=self.selected_row_color)
            path_label.configure(text_color=self.selected_text_color)
            self.selected_data[file_path] = widgets

    def curselection(self) -> tuple[int, ...]:
        """Returns indices of currently selected items."""
        return tuple(
            idx for idx, path in enumerate(self.all_rows) if path in self.selected_data
        )

    def move(self, *, direction: str, callback):
        """Moves selected items as a block in the specified direction."""
        sel_idxs = sorted(self.curselection())
        if not sel_idxs:
            return

        items = self.all_rows
        n = len(items)

        if direction == "down":
            # Check if the last selected item is already at the very bottom
            if sel_idxs[-1] < n - 1:
                # Iterate in reverse to avoid overwriting data while shifting down
                for i in reversed(sel_idxs):
                    items[i], items[i + 1] = items[i + 1], items[i]

        elif direction == "up":
            # Check if the first selected item is already at the very top
            if sel_idxs[0] > 0:
                # Iterate normally to shift items up
                for i in sel_idxs:
                    items[i], items[i - 1] = items[i - 1], items[i]

        # Update visual representation using the smart refresh method
        self.refresh(file_list=items)

        if callback:
            callback()

    def clear(self):
        """Performs a full cleanup of all items and widgets."""
        for widgets in self.all_widgets.values():
            widgets["frame"].destroy()
        self.all_widgets.clear()
        self.selected_data.clear()
        self.all_rows.clear()

    def clear_selection(self):
        """Resets the visual state of all selected items and clears the selection dictionary."""
        for path, widgets in self.selected_data.items():
            widgets["frame"].configure(fg_color="transparent")
            widgets["label"].configure(text_color=self.default_text_color)
        self.selected_data.clear()

    def get_selected_paths(self) -> list[Path]:
        """Returns a list of currently selected file paths."""
        return list(self.selected_data.keys())

    def _bind_mouse_wheel(self, widget):
        """Links any widget inside the listbox to the smooth scroll engine."""
        widget.bind("<MouseWheel>", self._handle_mouse_wheel)
        widget.bind("<Button-4>", self._handle_mouse_wheel)  # Linux Support
        widget.bind("<Button-5>", self._handle_mouse_wheel)  # Linux Support'

    def _smooth_scroll_engine(self):
        """Calculates and applies smooth movement using fractional offsets."""
        if abs(self._scroll_target) > 0.001:
            # We determine how much of the total content height one pixel represents
            # scroll_region format: (x1, y1, x2, y2)
            region = self._parent_canvas.cget("scrollregion")
            if not region:
                return

            total_height = float(region.split()[-1])
            if total_height <= 0:
                return

            # Calculate the fraction to move (shift in pixels / total height)
            shift_fraction = (self._scroll_target * 0.2) / total_height

            # Get current position and apply the shift
            current_pos = self._parent_canvas.yview()[0]
            new_pos = current_pos + shift_fraction

            # Clamp the value between 0 and 1
            new_pos = max(0.0, min(1.0, new_pos))

            self._parent_canvas.yview_moveto(new_pos)

            # Reduce the target
            self._scroll_target -= self._scroll_target * 0.2
            self.after(10, self._smooth_scroll_engine)
        else:
            self._scroll_target = 0
            self._is_scrolling = False

    def _handle_mouse_wheel(self, event):
        """Captures the scroll intent and starts the engine."""
        # Determine the scroll amount
        if event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            delta = -50  # Upward force
        else:
            delta = 50  # Downward force

        self._scroll_target += delta

        # Start the animation loop if it's not already running
        if not self._is_scrolling:
            self._is_scrolling = True
            self._smooth_scroll_engine()
