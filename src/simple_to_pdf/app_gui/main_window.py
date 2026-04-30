import logging
import os
import subprocess
import sys
import customtkinter as ctk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Callable
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.app_gui.gui_callback import GUICallback
from simple_to_pdf.app_gui.help_frame import HelpFrame
from simple_to_pdf.app_gui.list_controls_frame import ListControlsFrame
from simple_to_pdf.app_gui.main_frame import MainFrame
from simple_to_pdf.app_gui.settings_frame import SettingsFrame
from simple_to_pdf.cli.logger import get_log_dir
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.pdf import PageExtractor, PdfMerger
from simple_to_pdf.utils.file_tools import get_files
from simple_to_pdf.utils.logic import get_pages
from simple_to_pdf.utils.ui_tools import change_state, ui_locker
from simple_to_pdf.utils.notification_manager import NotificationManager
from simple_to_pdf.app_dialog import (
    AboutDialog,
    UpdateDialog,
    PageSelectionDialog,
)
from simple_to_pdf.core import config
from simple_to_pdf.app_gui.base_window import BaseWindow

logger = logging.getLogger(__name__)


class PDFMergerGUI(BaseWindow):
    def __init__(
        self,
        *,
        merger: PdfMerger,
        page_extractor: PageExtractor,
        version_controller: VersionController,
    ):

        # Initialize BaseWindow
        super().__init__(title=f"{config.APP_NAME}-PDF Merger", size="1000x700")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.thread_running: bool = False
        self.merger: PdfMerger = merger
        self.page_extractor: PageExtractor = page_extractor
        self.version_controller: VersionController = version_controller
        self.notifier: NotificationManager = NotificationManager(self)
        # build UI inside root_container inherited from BaseWindow

        handlers = self._setup_handlers()
        self.init_panels(callback=handlers)
        self.init_connections()
        self.build_gui(callbacks=handlers)

    def init_panels(self, callback: dict[str, Callable]) -> None:
        self.main_panel: MainFrame = MainFrame(
            master=self.root_container,
            merger=self.merger,
            notifier=self.notifier,
            callbacks=callback,
        )
        self.btns_panel: ListControlsFrame = ListControlsFrame(
            self.root_container, callbacks=callback
        )
        self.settings_panel: SettingsFrame = SettingsFrame(
            parent=self.root_container, callbacks=callback
        )
        self.help_panel: HelpFrame = HelpFrame(
            parent=self.root_container, callbacks=callback
        )

    def init_connections(self) -> None:
        self.callback = GUICallback(main_frame=self.main_panel)

    # TODO Add a separate toggle_ui function for each panel.
    def toggle_ui(self, *, active: bool) -> None:
        """Enable or disable the entire UI."""

        if active:
            btns_state = ctk.NORMAL
        else:
            btns_state = ctk.DISABLED

        # Disable all buttons and menu items
        change_state(widgets_dict=self.btns_panel.ui, state=btns_state)

    def build_gui(self, *, callbacks: dict[str, Callable]) -> None:
        """Builds the main GUI layout"""

        # Side-by-side layout with padding

        self.help_panel.pack(side="right", fill="y", padx=(0, 10), pady=20)
        self.settings_panel.pack(side="right", fill="y", padx=(0, 10), pady=20)
        self.btns_panel.pack(side="right", fill="y", padx=(10, 10), pady=20)
        self.main_panel.pack(
            side="left", fill="both", expand=True, padx=(20, 10), pady=20
        )

    def open_log_folder(self):
        """Handles the OS-specific logic to open the file explorer."""

        # Primary path in the user's home directory
        log_dir = get_log_dir()

        # Get the absolute path as a string
        path_str = str(log_dir.absolute())

        if sys.platform == "win32":
            # On Windows, os.startfile handles the explorer process correctly
            try:
                os.startfile(path_str)
            except Exception as e:
                logger.error(f"Could not open folder on Windows: {e}")

        elif sys.platform == "linux":
            # Create a clean environment copy to avoid library conflicts
            # PyInstaller sets LD_LIBRARY_PATH which can break system apps like xdg-open
            clean_env = os.environ.copy()

            # Remove variables that might point to the bundled PyInstaller libraries
            vars_to_remove = ["LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONHOME"]
            for var in vars_to_remove:
                clean_env.pop(var, None)

            try:
                # Use xdg-open with the cleaned environment
                subprocess.Popen(
                    ["xdg-open", path_str],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=clean_env,  # Critical for bundled Linux applications
                )
            except Exception as e:
                logger.error(f"Could not open folder on Linux: {e}", exc_info=True)

    def _setup_handlers(self) -> dict[str, Callable]:
        """
        Central registry of all UI commands.
        Using lambdas for panel methods to ensure they are resolved only when clicked.
        """
        return {
            "merge": self.on_merge,
            "extract": self.prompt_pages_to_remove,
            "license": self.show_license,
            "about": self.show_about,
            "update": self.on_check_updates_click,
            "logs": self.open_log_folder,
            "documentation": self.show_documentation,
            "add": lambda: self.main_panel.add_files(),
            "remove": lambda: self.main_panel.remove_files(),
            "clear_status": lambda: self.main_panel.clear_status_text(),
            "move": lambda direction: self.main_panel.move_on_listbox(
                direction=direction
            ),
            "settings": lambda: self.settings_panel.toggle(),
            "help": lambda: self.help_panel.toggle(),
            "change_language": lambda lang: self.on_change_language(lang),
        }

    def on_change_language(self, new_lang_name: str) -> None:
        """Handler for language changes from the interface."""
        LocalizationMixin.switch_language(new_lang_name)

    # Pass this callback to the settings:
    callbacks = {"change_language": on_change_language}

    def on_check_updates_click(self):
        """
        Handles the update check event from the UI.
        """
        # Fetch data from controller
        result = self.version_controller.check_for_updates()

        # Handle errors
        if result.error_message:
            self.notifier.error(
                scenario_key="update_error",
            )
            return

        # If update found, show the beautiful dialog
        if result.is_available and result.release:
            UpdateDialog(self, result.release.version, result.release.notes)

        # If no update found
        else:
            current_v = self.version_controller._get_current_version()
            self.notifier.info(scenario_key="no_updates", version=current_v)

    def show_about(self):
        """Gathers data and displays the About Dialog."""
        # Get version from controller
        current_version = self.version_controller._get_current_version()

        # Get engine name
        engine_class = getattr(self.merger.converter, "__class__", None)
        engine_name = engine_class.__name__ if engine_class else "Unknown"

        # Open the dialog
        AboutDialog(self, current_version, engine_name)

    def show_license(self) -> None:
        """Displays the license file in a styled TextWindow."""
        license_path = config.LICENCE_PATH
        cur_year = datetime.now().year

        # Check if file exists
        if not license_path.exists():
            logger.warning(f"⚠️ License file not found at path: {license_path}")
            self.notifier.warning(scenario_key="file_not_found")
            return
        try:
            # Reading file (UTF-8 is essential for cross-platform compatibility)
            text = license_path.read_text(encoding="utf-8")
            formatted_text = text.format(year=cur_year)

            # Call the new class instead of the old method
            self.notifier.info(
                text=formatted_text,
                scenario_key="license_info",
                font_size=14,
                size="750x600",
                year=cur_year,
                app_name=config.APP_NAME,
                with_footer=True,
            )

        except Exception as e:
            logger.error(f"❌ Error reading license file: {e}")
            self.notifier.error(
                scenario_key="file_read_error",
                file_name=license_path,
            )

    def show_documentation(self) -> None:
        webbrowser.open(config.README_URL)

    def on_merge(self):
        """Handler for Merge button click"""

        # Preparing data (quick operation, doing in main thread)
        files = [[i, path] for i, path in enumerate(self.main_panel.filebox.all_rows)]
        if not files:
            self.notifier.warning(
                scenario_key="no_file_to_merge",
            )
            return

        out = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="merged.pdf",
        )
        if not out:
            return

        self._run_merge_worker(files=files, output_path=out)

    @ui_locker
    def _run_merge_worker(self, files, output_path):
        try:
            # Reset progress bar
            self.main_panel.progress_bar_reset()

            # Give this safe wrapper to the engine
            self.merger.merge_to_pdf(
                files=files,
                output_path=output_path,
                callback=self.callback.safe_callback,  # Use the wrapper
            )

        except Exception as e:
            err_msg = f"❌ Error: Could not merge files: \n{e}"
            logger.error(err_msg, exc_info=True)
            self.main_panel.progress_bar_reset()

    def prompt_pages_to_remove(self):
        """Select a PDF file and show the page extraction dialog."""
        input_path = get_files(filetypes=[("PDF files", "*.pdf")], multiple=False)
        if not input_path:
            return

        # Refresh the main window to prevent UI freezing before showing the dialog
        self.update()

        # Initialize and display the selection dialog
        dialog = PageSelectionDialog(self)
        raw_input = dialog.get_input()

        # Proceed if the user provided input and didn't cancel
        if raw_input:
            self.on_confirm(raw_input=raw_input, input_path=input_path)

    def on_confirm(self, *, raw_input: str, input_path) -> None:
        # Parse string input into a list of page indices
        pages = get_pages(raw=raw_input.strip())

        if pages is None:
            self.notifier.warning(
                scenario_key="wrong_page_format",
            )
            return

        # Validate page numbers against the actual PDF file
        try:
            self.page_extractor.validate_pages(
                input_path=Path(input_path), pages_to_extract=pages
            )
        except ValueError as e:
            self.notifier.error(
                scenario_key="page_validation_error",
                error=e,
            )
            return
        except Exception as e:
            self.notifier.error(
                scenario_key="file_read_error",
                file_name=input_path,
            )
            return

        # Ask user for the output destination
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"extracted_{Path(input_path).stem}.pdf",
            title="Save PDF",
        )

        if not output_path:
            return

        self._run_page_extractor_worker(
            input_path=input_path, pages=pages, output_path=output_path
        )

    @ui_locker
    def _run_page_extractor_worker(self, input_path, pages, output_path):
        try:
            # Reset progress bar
            self.main_panel.progress_bar_reset()
            self.page_extractor.extract_pages(
                input_path=input_path,
                pages_to_extract=pages,
                output_path=output_path,
                callback=self.callback.safe_callback,
            )
            self.callback.set_status(
                key="extract.done", status="success", path=output_path
            )

        except Exception as e:
            error_msg = f"❌ Error during page extraction: {e}"
            if isinstance(e, ValueError):
                self.after(
                    0,
                    lambda: self.notifier.error(
                        scenario_key="page_extraction_error",
                        file_name=input_path,
                    ),
                )
            else:
                self.callback.set_status(key="extract.error", status="error", error=e)
                logger.error(error_msg, exc_info=True)
                self.after(0, lambda: self.main_panel.progress_bar_reset())

    def _on_closing(self):
        if self.thread_running:
            self.notifier.warning(
                scenario_key="process_in_progress",
                with_icon=True,
            )
            self._wait_for_thread_finish()
        else:
            self.destroy()

    def _wait_for_thread_finish(self):
        """
        Periodically checks if the background thread has finished its work
        before allowing the application to close.
        """
        if self.thread_running:
            # Polling every 100ms
            logger.info(
                "Waiting for background thread to finish... (re-checking in 1s)"
            )
            self.after(1000, self._wait_for_thread_finish)
        else:
            logger.info("Background thread finished. Closing the application.")
            self.destroy()
