from simple_to_pdf.utils.theme_provider import ThemeProviderMixin
from simple_to_pdf.widgets import BaseFrame, BaseLabel
from pathlib import Path
import customtkinter as ctk


class CTkListbox(ctk.CTkScrollableFrame, ThemeProviderMixin):
    def __init__(self, parent, **kwargs):
        params = self.set_scrollable_frame_params(scr_frame_type="file_list")
        params.update(kwargs)
        super().__init__(parent, **params)

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

    def _create_file_row(self, parent, *, file_path: Path):
        row = BaseFrame(parent, frame_type="list_item")
        row.pack(fill="x", padx=5, pady=2)
        path_text = str(file_path)
        path_label = BaseLabel(row, label_type="content", anchor="w", justify="left")
        path_label.pack(
            side="left", text=path_text, fill="x", expand=True, padx=(10, 5)
        )

        def on_click(event):
            self._select_row(row_frame=row, file_path=file_path)

        row.bind("<Button-1>", on_click)
        path_label.bind("<Button-1>", on_click)

    def _select_row(self, *, row_frame, file_path):

        if hasattr(self, "current_selected_row") and self.current_selected_row:
            self.current_selected_row.configure(fg_color="transparent")

        self.current_selected_row = row_frame
        self.current_selected_path = file_path

        row_frame.configure(fg_color="#334155")  # Наприклад, Slate 700
