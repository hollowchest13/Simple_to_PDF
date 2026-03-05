import logging
import tkinter as tk
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from pathlib import Path
from simple_to_pdf.pdf.pdf_merger import PdfMerger
from simple_to_pdf.utils.file_tools import get_files
from simple_to_pdf.utils.ui_tools import (
    clear_text_widget,
    get_selected_values,
    list_update,
    listbox_clear,
    reselect_items,
)
from simple_to_pdf.widgets import BaseFrame, BaseLabel, BaseTextBox
from simple_to_pdf.widgets import BaseProgress, BaseScrollableFrame, CTkListbox


logger = logging.getLogger(__name__)


class MainFrame(BaseFrame):
    def __init__(self, parent: tk.Frame, merger: PdfMerger):
        super().__init__(parent)
        self.merger = merger
        self.ui: dict[str, tk.Widget] = {}
        self.status_text: BaseTextBox
        self.filebox: CTkListbox
        self.progress_bar: BaseProgress
        self.progress_label: BaseLabel

        # Set attributes and register in self.ui
        self._register_components(self._setup_layout())

    def _setup_layout(self):
        raw_components = {}
        LEFT_SIDE_PAD: int = 10
        RIGHT_SIDE_PAD: int = 10
        TOP_SIDE_PAD: int = 5
        BOTTOM_SIDE_PAD: int = 10

        status_area = BaseFrame(self)
        status_area.pack(
            side="bottom",
            fill="x",
            padx=(LEFT_SIDE_PAD, RIGHT_SIDE_PAD),
            pady=(TOP_SIDE_PAD, BOTTOM_SIDE_PAD),
        )

        file_batch_area = BaseFrame(self, frame_type="scr_frame_container")
        file_batch_area.pack(
            fill="both",
            expand=True,
            padx=(LEFT_SIDE_PAD, RIGHT_SIDE_PAD),
            pady=(TOP_SIDE_PAD, BOTTOM_SIDE_PAD),
        )

        progress_area = BaseFrame(self)
        progress_area.pack(
            side="top",
            fill="x",
            padx=(LEFT_SIDE_PAD, RIGHT_SIDE_PAD),
            pady=(TOP_SIDE_PAD, BOTTOM_SIDE_PAD),
        )

        # Create and register all components
        raw_components = {
            "filebox": self._setup_file_batch_area(mid=file_batch_area),
            "status_text": self._setup_status_area(status_frame=status_area),
        }

        # Then build progress bar and label because it returns two widgets
        p_bar, p_label = self._setup_progress_bar_area(progress_frame=progress_area)
        raw_components["progress_bar"] = p_bar
        raw_components["progress_label"] = p_label
        return raw_components

    def _register_components(self, components: dict[str, tk.Widget]):
        """Adds components to self and self.ui for easy access."""

        for key, widget in components.items():
            setattr(self, key, widget)
            self.ui[key] = widget

    def _setup_file_batch_area(self, mid: BaseFrame) -> CTkListbox:
        """Builds the central scrollable area for displaying files using CustomTkinter."""
        filebox: CTkListbox = CTkListbox(mid, label_text="Selected Files")
        filebox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        return filebox

    def _setup_status_area(self, status_frame: ctk.CTkFrame) -> ctk.CTkTextbox:
        text: BaseTextBox = BaseTextBox(status_frame, textbox_type="status_text")
        text.pack(side="bottom", fill="x", expand=True)
        return text

    def _setup_progress_bar_area(
        self, progress_frame: ctk.CTkFrame
    ) -> tuple[BaseProgress, ctk.CTkLabel]:

        label = BaseLabel(progress_frame, text="Progress:", label_type="badge")
        label.pack(pady=4)

        bar = BaseProgress(
            progress_frame, progress_type="merge_progress", mode="determinate"
        )
        empty_track_color = bar.cget("fg_color")
        bar.configure(progress_color=empty_track_color)
        bar.set(0)
        bar.pack(pady=8, fill="x")
        return bar, label

    def clear_status_text(self) -> None:
        content = self.status_text.get("1.0", "end-1c")
        if content.strip():
            clear_text_widget(self.status_text)

    def _get_formatted_filetypes(self) -> list[tuple[str, str]]:
        """Converts a dictionary of formats into a list of tuples for the dialog window."""

        supported_dict = self.merger.converter.get_supported_formats()
        formatted_types = []

        # 1.Get all extensions for the general filter
        all_exts = []
        for exts in supported_dict.values():
            all_exts.extend(exts)

        # Create a string like "*.pdf *.docx *.png"
        all_pattern = " ".join([f"*{e}" for e in all_exts])
        formatted_types.append(("All supported files", all_pattern))

        # 2. Add each category separately
        # Sort keys so PDF is always at the top or logically first
        for category in sorted(supported_dict.keys()):
            exts = supported_dict[category]
            label = f"{category.capitalize()} files"
            pattern = " ".join([f"*{e}" for e in exts])
            formatted_types.append((label, pattern))
        return formatted_types

    # Add files to the listbox
    def add_files(self):
        """Add files of selected types."""

        # Supported list the extensions
        types = self._get_formatted_filetypes()
        new_files_paths: list[str] = list(get_files(filetypes=types, multiple=True))

        if not new_files_paths:
            return

        # Call the method. It will create "All supported" files
        # saved_files_paths: list[str] = self.filebox.get_files()

        files_paths: list[str] = new_files_paths

        if files_paths:
            self.progress_bar_reset()
            self.filebox.add_new_files(file_list=files_paths)

    def remove_files(self) -> None:
        all_files = self.filebox.all_rows
        sel_files = self.filebox.get_selected_paths()
        if not all_files:
            CTkMessagebox(
                master=self.winfo_toplevel(),
                title="No files",
                message="The file list is already empty.",
                icon="info",
                option_1="OK",
            )
            return
        elif not sel_files:
            msg = CTkMessagebox(
                master=self.winfo_toplevel(),
                title="No files.",
                message="No files selected. Do you want to remove all files?",
                icon="question",
                option_1="No",
                option_2="Yes",
            )
            answer = msg.get()

            if answer == "Yes":
                self.filebox.clear(callback=self.reset_progress_widgets)
                return
        self.filebox.remove_selected(callback=self.progress_bar_reset)

    def reset_progress_widgets(self):
        self.progress_bar_reset()
        self.clear_status_text()

    def move_on_listbox(self, *, direction: str):
        """Move selected items up or down in the listbox."""

        self.filebox.move(direction=direction, callback=self.progress_bar_reset)

    def progress_bar_reset(self):
        self.set_progress_determinate()
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=self.progress_bar.cget("fg_color"))
        self.progress_label.configure(text="Progress: Ready")
        self.update_idletasks()

    def set_progress_determinate(self):
        """
        Safely switches the progress bar to determinate mode.
        This method should be called via .after() if triggered from a worker thread.
        """
        if self.progress_bar.winfo_exists():
            self.progress_bar.stop()  # Stop indeterminate animation
            self.progress_bar.configure(mode="determinate")
            self.update_idletasks()  # Refresh the UI immediately
