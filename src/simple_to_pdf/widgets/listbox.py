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
        self.selected_data = {}

        self.selected_row = None
        self.selected_label = None
        self.default_text_color = self.get_color(ThemeKeys.TEXT_PRIMARY)
        self.selected_row_color = self.get_color(ThemeKeys.TEXT_PRIMARY)
        self.selected_text_color = self.get_color(ThemeKeys.TEXT_ON_ACCENT)

    def refresh(self, file_list: list[str]):
        for path in file_list:
            file_path = Path(path)
            self._create_file_row(parent=self, file_path=file_path)

    def get_selected(self) -> list[str]:
        return ["23"]

    def get_files(self) -> list[str]:
        return ["23"]

    def clear(self):
        pass

    def remove_item(self):
        pass

    def curselection(self) -> tuple[int, ...]:
        return (1, 2)

    def reselect_items(self, *, all_items, selected_values):
        pass

    def _create_file_row(self, parent, *, file_path: Path):
        row = BaseFrame(parent, frame_type="list_item", border_width=1)
        row.pack(fill="x", padx=5, pady=2)
        path_text = str(file_path)
        path_label = BaseLabel(
            row, text=path_text, label_type="content", anchor="w", justify="left"
        )
        path_label.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=5)

        def on_click(event):
            self._select_row(row_frame=row, file_path=file_path, path_label=path_label)

        row.bind("<Button-1>", on_click)
        path_label.bind("<Button-1>", on_click)

    def _select_row(
        self, *, row_frame: ctk.CTkFrame, file_path: Path, path_label: ctk.CTkLabel
    ):

        if file_path in self.selected_data:
            # Reset unselected frame color
            row_frame.configure(fg_color="transparent")
            # Reset unselected label color
            path_label.configure(text_color=self.default_text_color)
            del self.selected_data[file_path]
        else:
            row_frame.configure(fg_color=self.selected_row_color)
            path_label.configure(text_color=self.selected_text_color)
            self.selected_data[file_path] = {"frame": row_frame, "label": path_label}

    def get_selected_paths(self) -> list[Path]:
        # Return list of selected file paths in selection order
        return list(self.selected_data.keys())

    def clear_selection(self):
        for data in self.selected_data.values():
            data["frame"].configure(fg_color="transparent")
            data["label"].configure(text_color=self.default_text_color)
        self.selected_data.clear()
