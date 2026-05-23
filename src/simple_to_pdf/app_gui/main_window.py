import logging
import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Dict, List

import customtkinter as ctk

from simple_to_pdf.app_dialog import (
    AboutDialog,
    PageSelectionDialog,
    UpdateDialog,
)
from simple_to_pdf.app_gui.base_window import BaseWindow
from simple_to_pdf.app_gui.gui_callback import GUICallback
from simple_to_pdf.app_gui.help_frame import HelpFrame
from simple_to_pdf.app_gui.list_controls_frame import ListControlsFrame
from simple_to_pdf.app_gui.main_frame import MainFrame
from simple_to_pdf.app_gui.settings_frame import SettingsFrame
from simple_to_pdf.cli.logger import get_log_dir
from simple_to_pdf.core import config
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.pdf import PageExtractor, PDFCompressor, PdfMerger
from simple_to_pdf.settings.settings_manager import SettingsManager
from simple_to_pdf.utils.file_tools import FileToolKit, get_files
from simple_to_pdf.utils.logic import get_selected_pages
from simple_to_pdf.utils.notification_manager import NotificationManager
from simple_to_pdf.utils.ui_tools import change_state, ui_locker
from simple_to_pdf.widgets import BaseFrame, ToogleFrame

logger = logging.getLogger(__name__)


class PDFMergerGUI(BaseWindow):
    """Main GUI window for the PDF merger application."""

    def __init__(
        self,
        *,
        merger: PdfMerger,
        page_extractor: PageExtractor,
        version_controller: VersionController,
        settings_manager: SettingsManager,
        compressor: PDFCompressor,
    ):
        """Create the main window and wire its dependencies."""

        super().__init__(title=f"{config.APP_NAME}-PDF Merger", size="1000x700")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.thread_running: bool = False
        self.merger = merger
        self.page_extractor = page_extractor
        self.version_controller = version_controller
        self.compressor = compressor
        self.notifier = NotificationManager(self)
        self.settings_manager = settings_manager

        handlers = self._setup_handlers()
        self.init_panels(handlers=handlers)
        self.init_connections()
        self.build_gui()
        self.setup_language()

    def init_panels(self, handlers: dict[str, Callable]) -> None:
        """Create the window panels."""
        self.main_panel: MainFrame = MainFrame(
            master=self.root_container,
            merger=self.merger,
            notifier=self.notifier,
            handlers=handlers,
        )
        self.btns_panel: ListControlsFrame = ListControlsFrame(
            self.root_container, handlers=handlers
        )
        self.dynamic_side_panel: BaseFrame = BaseFrame(
            self.root_container, frame_type="scr_frame_container"
        )
        self.settings_panel: SettingsFrame = SettingsFrame(
            self.dynamic_side_panel, handlers=handlers, is_open=True
        )
        self.help_panel: HelpFrame = HelpFrame(
            self.dynamic_side_panel, handlers=handlers
        )
        self.slide_tabs: List[ToogleFrame] = [self.settings_panel, self.help_panel]

    def init_connections(self) -> None:
        """Attach callbacks to processing components."""
        self.callback = GUICallback(main_frame=self.main_panel)
        self.merger.callback = self.callback.safe_callback
        self.page_extractor.callback = self.callback.safe_callback
        self.compressor.callback = self.callback.safe_callback

    def toggle_ui(self, *, active: bool) -> None:
        """Enable or disable the window controls."""
        if active:
            state = ctk.NORMAL
        else:
            state = ctk.DISABLED

        change_state(widgets_dict=self.btns_panel.ui, state=state)
        change_state(widgets_dict=self.settings_panel.ui, state=state)

    def build_gui(self) -> None:
        """Lay out the main panels."""
        self.dynamic_side_panel.pack(side="right", fill="y", padx=(0, 10), pady=20)
        self.btns_panel.pack(side="right", fill="y", padx=(10, 10), pady=20)
        self.main_panel.pack(
            side="left", fill="both", expand=True, padx=(20, 10), pady=20
        )
        self.settings_panel.pack(side="right", fill="y", pady=10, padx=10)

    def open_log_folder(self) -> None:
        """Open the log directory in the system file explorer."""
        log_dir = get_log_dir()
        path_str = str(log_dir.absolute())

        if sys.platform == "win32":
            try:
                os.startfile(path_str)
            except Exception as e:
                logger.error(f"Could not open folder on Windows: {e}")

        elif sys.platform == "linux":
            clean_env = os.environ.copy()
            vars_to_remove = ["LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONHOME"]
            for var in vars_to_remove:
                clean_env.pop(var, None)

            try:
                subprocess.Popen(
                    ["xdg-open", path_str],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=clean_env,
                )
            except Exception as e:
                logger.error(f"Could not open folder on Linux: {e}", exc_info=True)

    def _setup_handlers(self) -> dict[str, Callable]:
        """Build the UI command map."""
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
            "settings": lambda: self.toogle_tab(
                target_panel=self.settings_panel, panel_list=self.slide_tabs
            ),
            "help": lambda: self.toogle_tab(
                target_panel=self.help_panel, panel_list=self.slide_tabs
            ),
            "change_language": lambda lang: self.on_change_language(lang),
        }

    def toogle_tab(
        self, *, target_panel: ToogleFrame, panel_list: list[ToogleFrame]
    ) -> None:
        """Toggle one side panel and close the others."""
        if target_panel.is_open:
            return
        for panel in panel_list:
            if panel != target_panel and panel.is_open:
                panel.toggle()
        target_panel.toggle()

    def setup_language(self) -> None:
        """Load and apply the saved language."""
        settings = self.settings_manager.get_settings()
        self.lang = settings.get("language", "Українська")
        if "language_selector" in self.settings_panel.ui:
            lang_selector = self.settings_panel.ui["language_selector"]
            lang_selector.set(self.lang)
            self.on_change_language(self.lang)

    def on_change_language(self, new_lang_name: str) -> None:
        """Apply a selected UI language across the application."""
        LocalizationMixin.switch_language(lang_name=new_lang_name)

    def on_check_updates_click(self) -> None:
        """Check whether a newer release is available and inform the user."""
        result = self.version_controller.check_for_updates()

        if result.error_message:
            self.notifier.error(
                scenario_key="update_error",
            )
            return

        if result.is_available and result.release:
            UpdateDialog(self, result.release.version, result.release.notes)
        else:
            current_v = self.version_controller._get_current_version()
            self.notifier.info(scenario_key="no_updates", version=current_v)

    def show_about(self) -> None:
        """Gather application metadata and display the About dialog."""
        current_version = self.version_controller._get_current_version()
        engine_class = getattr(self.merger.converter, "__class__", None)
        engine_name = engine_class.__name__ if engine_class else "Unknown"
        AboutDialog(self, current_version, engine_name)

    def show_license(self) -> None:
        """Display the license text in the notification dialog."""
        license_path = config.LICENCE_PATH
        cur_year = datetime.now().year

        if not license_path.exists():
            logger.warning(f"⚠️ License file not found at path: {license_path}")
            self.notifier.warning(scenario_key="file_not_found")
            return

        try:
            text = license_path.read_text(encoding="utf-8")
            formatted_text = text.format(year=cur_year)
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
            logger.error(f"Error reading license file: {e}")
            self.notifier.error(
                scenario_key="file_read_error",
                file_name=license_path,
            )

    def show_documentation(self) -> None:
        """Open the project documentation in the default browser."""
        webbrowser.open(config.README_URL)

    def on_merge(self) -> None:
        """Start the merge workflow and ask the user where to save the result."""
        files: list[tuple[int, Path]] = [
            (i, path) for i, path in enumerate(self.main_panel.filebox.all_rows)
        ]
        if not files:
            self.notifier.warning(scenario_key="no_file_to_merge")
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
    def _run_merge_worker(
        self, files: List[tuple[int, Path]], output_path: str
    ) -> None:
        """Merge the selected files, optionally compress the result, and save it."""
        self.main_panel.progress_bar_reset()
        try:
            self.callback.safe_callback(
                "progress",
                **{
                    "stage": "merging",
                    "mode": "indeterminate",
                },
            )
            merge_res = self.merger.merge_to_pdf(files=files)
            self.callback.safe_callback(
                "status",
                **{
                    "key": "merge.done",
                    "status": "info" if merge_res.failed == 0 else "warning",
                    "success": merge_res.success,
                    "failed": merge_res.failed,
                },
            )
            data = merge_res.data
        except Exception as e:
            logger.error(f"Merge stage failed: {e}", exc_info=True)
            self.callback.safe_callback(
                "status", **{"key": "merge.error", "status": "error", "error": e}
            )
            return

        need_compress: bool = self.settings_panel.compress_selector.is_on()
        if need_compress:
            self.callback.safe_callback(
                "progress",
                **{
                    "stage": "compressing",
                    "mode": "indeterminate",
                },
            )
            data = self.compressor.compress(pdf_bytes=data)

        try:
            FileToolKit.write_bytes(bytes_data=data, file_path=Path(output_path))
            self.callback.safe_callback(
                "status",
                **{"key": "save.done", "status": "info", "path": output_path},
            )
        except OSError as e:
            logger.error(f"Saving stage failed (OS Error): {e}", exc_info=True)
            self.callback.safe_callback(
                "status",
                **{
                    "key": "save.error.permission",
                    "status": "error",
                    "path": "output_path",
                },
            )
        except Exception as e:
            logger.error(f"Saving stage failed (Unknown Error): {e}", exc_info=True)
            self.callback.safe_callback(
                "status", **{"key": "save.error.unknown", "status": "error"}
            )

    def prompt_pages_to_remove(self) -> None:
        """Prompt the user to select a PDF and choose pages for extraction."""
        input_path = get_files(filetypes=[("PDF files", "*.pdf")], multiple=False)
        if not input_path:
            return

        self.update()

        dialog = PageSelectionDialog(self)
        raw_input = dialog.get_input()

        if raw_input:
            self.on_confirm(raw_input=raw_input, input_path=input_path)

    def on_confirm(self, *, raw_input: str, input_path) -> None:
        """Validate page selection input and launch the extraction workflow."""
        pages = get_selected_pages(raw=raw_input.strip())

        if pages is None:
            self.notifier.warning(scenario_key="wrong_page_format")
            return

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
        except Exception:
            self.notifier.error(
                scenario_key="file_read_error",
                file_name=input_path,
            )
            return

        clean_tag = raw_input.strip()
        short_tag = clean_tag[:30] + "..." if len(clean_tag) > 30 else clean_tag
        suggested_name = f"pages_{short_tag}_from_{Path(input_path).stem}.pdf"

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=suggested_name,
            title="Save PDF",
        )

        if not output_path:
            return

        self._run_page_extractor_worker(
            input_path=input_path, pages=pages, output_path=output_path
        )

    @ui_locker
    def _run_page_extractor_worker(self, input_path, pages, output_path) -> None:
        """Run the page-extraction worker and report progress or errors."""
        try:
            self.main_panel.progress_bar_reset()
            self.page_extractor.extract_pages(
                input_path=input_path,
                pages_to_extract=pages,
                output_path=output_path,
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

    def _on_closing(self) -> None:
        """Handle window close requests and wait for background work if needed."""
        if self.thread_running:
            self.notifier.warning(
                scenario_key="process_in_progress",
                with_icon=True,
            )
            self._wait_for_thread_finish()
        else:
            self._save_and_destroy()

    def _wait_for_thread_finish(self) -> None:
        """Poll until any background work finishes before closing the window."""
        if self.thread_running:
            logger.info(
                "Waiting for background thread to finish... (re-checking in 1s)"
            )
            self.after(1000, self._wait_for_thread_finish)
        else:
            logger.info("Background thread finished. Closing the application.")
            self._save_and_destroy()

    def _save_and_destroy(self) -> None:
        """Persist current settings and destroy the main window."""
        settings: Dict[str, str] = self.settings_panel.collect_data()
        self.settings_manager.save_settings(settings=settings)
        self.destroy()
