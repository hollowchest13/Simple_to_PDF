import logging
import tkinter as tk
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from typing import Callable, Dict, Any, Tuple

from simple_to_pdf.pdf.pdf_merger import PdfMerger
from simple_to_pdf.utils.file_tools import get_files
from simple_to_pdf.utils.notification_manager import NotificationManager
from simple_to_pdf.utils.ui_tools import (
    clear_text_widget,
)
from simple_to_pdf.app_dialog import ConfirmDialog
from simple_to_pdf.utils.notification_manager import NotificationManager
from simple_to_pdf.widgets import (
    BaseFrame,
    BaseLabel,
    BaseTextBox,
    BaseProgress,
    CTkListbox,
)

logger = logging.getLogger(__name__)


class MainFrame(BaseFrame):
    def __init__(
        self,
        *,
        master: tk.Frame,
        merger: PdfMerger,
        notifier: NotificationManager,
        callbacks: Dict[str, Callable],
    ):
        super().__init__(master)
        self.merger = merger
        self.notifier = notifier
        self.callbacks = callbacks
        self.loc_section = "ui.main_panel"

        # Explicit type hints for IDE autocomplete
        self.status_text: BaseTextBox
        self.filebox: CTkListbox
        self.progress_bar: BaseProgress
        self.progress_label: BaseLabel

        # Dictionary for LocalizationMixin to track translatable widgets
        self.ui: Dict[str, Any] = {}

        # Build layout and register components into self and self.ui
        self._register_components(self._setup_layout())

        # Initialize localization observer
        self.init_localization()

    def _setup_layout(self) -> Dict[str, Any]:
        """Sets up the visual frames and returns a dictionary of created widgets."""
        raw_components = {}
        LEFT_SIDE_PAD: int = 10
        RIGHT_SIDE_PAD: int = 10
        TOP_SIDE_PAD: int = 5
        BOTTOM_SIDE_PAD: int = 10

        # 1. Status area container (Bottom)
        status_area = BaseFrame(self)
        status_area.pack(
            side="bottom",
            fill="x",
            padx=(LEFT_SIDE_PAD, RIGHT_SIDE_PAD),
            pady=(TOP_SIDE_PAD, BOTTOM_SIDE_PAD),
        )

        # 2. File list area container (Center)
        file_batch_area = BaseFrame(self, frame_type="scr_frame_container")
        file_batch_area.pack(
            fill="both",
            expand=True,
            padx=(LEFT_SIDE_PAD, RIGHT_SIDE_PAD),
            pady=(TOP_SIDE_PAD, BOTTOM_SIDE_PAD),
        )

        # 3. Progress area container (Top)
        progress_area = BaseFrame(self)
        progress_area.pack(
            side="top",
            fill="x",
            padx=(LEFT_SIDE_PAD, RIGHT_SIDE_PAD),
            pady=(TOP_SIDE_PAD, BOTTOM_SIDE_PAD),
        )

        # Create actual widgets and store in temporary dict
        raw_components["filebox"] = self._setup_file_batch_area(mid=file_batch_area)
        raw_components["status_text"] = self._setup_status_area(
            status_frame=status_area
        )

        p_bar, p_label = self._setup_progress_bar_area(progress_frame=progress_area)
        raw_components["progress_bar"] = p_bar
        raw_components["progress_label"] = p_label

        return raw_components

    def _register_components(self, components: Dict[str, Any]) -> None:
        """Adds components to self as attributes and to self.ui for localization."""
        for key, widget in components.items():
            setattr(self, key, widget)
            self.ui[key] = widget

    # --- Widget creation methods ---

    def _setup_file_batch_area(self, mid: BaseFrame) -> CTkListbox:
        """Builds the central scrollable area for displaying files."""
        filebox = CTkListbox(mid, label_text="Selected Files")
        filebox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        return filebox

    def _setup_status_area(self, status_frame: ctk.CTkFrame) -> BaseTextBox:
        """Builds the bottom status console."""
        text = BaseTextBox(status_frame, textbox_type="status_text")
        text.pack(side="bottom", fill="x", expand=True)
        return text

    def _setup_progress_bar_area(
        self, progress_frame: ctk.CTkFrame
    ) -> Tuple[BaseProgress, BaseLabel]:
        """Builds the top progress tracking section."""
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
        """Clears the status textbox content."""
        content = self.status_text.get("1.0", "end-1c")
        if content.strip():
            clear_text_widget(self.status_text)

    def _get_formatted_filetypes(self) -> list[tuple[str, str]]:
        """Prepares file extension filters for the dialog window."""
        supported_dict = self.merger.converter.get_supported_formats()
        formatted_types = []

        all_exts = []
        for exts in supported_dict.values():
            all_exts.extend(exts)

        all_pattern = " ".join([f"*{e}" for e in all_exts])
        formatted_types.append(("All supported files", all_pattern))

        for category in sorted(supported_dict.keys()):
            exts = supported_dict[category]
            label = f"{category.capitalize()} files"
            pattern = " ".join([f"*{e}" for e in exts])
            formatted_types.append((label, pattern))
        return formatted_types

    def add_files(self) -> None:
        """Opens file dialog and adds files to the listbox."""
        types = self._get_formatted_filetypes()
        new_files_paths: list[str] = list(get_files(filetypes=types, multiple=True))

        if not new_files_paths:
            return

        self.progress_bar_reset()
        self.filebox.add_new_files(file_list=new_files_paths)

    def remove_files(self) -> None:
        """Handles removal of selected files with confirmation dialogs."""
        all_files = self.filebox.all_rows
        sel_files = self.filebox.get_selected_paths()

        if not all_files:
            self.notifier.info(scenario_key="empty_file_list")
            return
        elif not sel_files:
            confirmed = ConfirmDialog.ask(
                parent=self.master, scenario_key="confirmation.confirm_delete"
            )

            if confirmed == True:
                self.filebox.clear(callback=self.reset_progress_widgets)
                return

        self.filebox.remove_selected(callback=self.progress_bar_reset)

    def reset_progress_widgets(self) -> None:
        """Full reset of progress and status UI."""
        self.progress_bar_reset()
        self.clear_status_text()

    def move_on_listbox(self, *, direction: str) -> None:
        """Shifts items in listbox and resets progress bar state."""
        self.filebox.move(direction=direction, callback=self.progress_bar_reset)

    def progress_bar_reset(self) -> None:
        """Resets the progress bar and label to 'Ready' state."""
        self.set_progress_determinate()
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=self.progress_bar.cget("fg_color"))
        self.progress_label.configure(
            text=self.get_text(key="main_panel.progress_label", section="ui")
        )
        self.update_idletasks()

    def set_progress_determinate(self) -> None:
        """Stops progress animations and sets to determinate mode."""
        if self.progress_bar.winfo_exists():
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.update_idletasks()
