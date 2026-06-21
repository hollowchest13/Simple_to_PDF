import logging
import os
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Any, Callable, Dict, List, Literal

import customtkinter as ctk

from simple_to_pdf.app_dialog import (
    AboutDialog,
    ConfirmDialog,
    PageSelectionDialog,
)
from simple_to_pdf.app_gui.base_window import BaseWindow
from simple_to_pdf.app_gui.gui_callback import GUICallback
from simple_to_pdf.app_gui.help_frame import HelpFrame
from simple_to_pdf.app_gui.list_controls_frame import ListControlsFrame
from simple_to_pdf.app_gui.main_frame import MainFrame
from simple_to_pdf.app_gui.settings_frame import SettingsFrame
from simple_to_pdf.cli.logger import get_log_dir
from simple_to_pdf.core import config
from simple_to_pdf.core.models import App_Mode
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.pdf import PageExtractor, PDFCompressor, PdfMerger
from simple_to_pdf.pdf.conversion_service import ConversionService
from simple_to_pdf.pdf.models import PageFormat
from simple_to_pdf.settings.settings_manager import SettingsManager
from simple_to_pdf.utils.file_tools import FileToolKit, get_files
from simple_to_pdf.utils.logic import get_selected_pages,InvalidPageInputError,PageLimitExceededError
from simple_to_pdf.utils.notification_manager import NotificationManager
from simple_to_pdf.utils.ui_tools import change_state, threaded_task
from simple_to_pdf.widgets import BaseFrame, ToogleFrame

logger = logging.getLogger(__name__)


class PDFMergerGUI(BaseWindow):
    """Main GUI window for the PDF merger application."""

    def __init__(
        self,
        *,
        conversion_service: ConversionService,
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
        self.conversion_service = conversion_service
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
        self.apply_settings()

    def apply_settings(self) -> None:
        self.settings_panel.setup()
        lang = self.settings_panel.get_widget_value(widget_id="language_selector")
        self.on_change_language(lang)

    def init_panels(self, handlers: dict[str, Callable]) -> None:
        """Create the window panels."""

        def get_formats():
            return self.conversion_service.converter.get_supported_formats()

        self.main_panel: MainFrame = MainFrame(
            master=self.root_container,
            get_supported_formats_func=get_formats,
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
            self.dynamic_side_panel,
            handlers=handlers,
            is_open=True,
            settings_manager=self.settings_manager,
        )
        self.help_panel: HelpFrame = HelpFrame(
            self.dynamic_side_panel, handlers=handlers
        )
        self.slide_tabs: List[ToogleFrame] = [self.settings_panel, self.help_panel]

    def init_connections(self) -> None:
        """Attach callbacks to processing components."""
        self.callback = GUICallback(main_frame=self.main_panel)
        self.conversion_service.callback = self.callback.safe_callback
        self.merger.callback = self.callback.safe_callback
        self.page_extractor.callback = self.callback.safe_callback
        self.compressor.callback = self.callback.safe_callback
        self.settings_panel.callback = self._update_merge_button

    def toggle_ui(self, *, active: bool) -> None:
        """Enable or disable the window controls."""

        state = ctk.NORMAL if active else ctk.DISABLED
        all_widgets = {**self.btns_panel.ui, **self.settings_panel.ui}
        stop_btn = all_widgets.pop("btn_stop", None)
        change_state(widgets_dict=all_widgets, state=state)
        if stop_btn:
            if active:
                stop_btn.configure(state=ctk.DISABLED)
            else:
                stop_btn.configure(state=ctk.NORMAL)

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
            "dependencies": self.show_dependencies,
            "add": self.add_files,
            "remove": self.remove_files,
            "stop": lambda: self._manage_services(action="stop"),
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

    def clear_console(self):
        self.main_panel.clear_status_text()

    @staticmethod
    def update_ui_after(method_name: str):
        def decorator(func: Callable[..., Any]):
            def wrapper(self, *args, **kwargs):
                result = func(self, *args, **kwargs)
                getattr(self, method_name)()
                return result

            return wrapper

        return decorator

    def _update_merge_button(self):
        """
        Update the state and mode of the merge/action button based on file selection.

        Analyzes the currently selected files to determine the appropriate
        application mode (COMPRESS, MERGE, or CONVERT) and toggles the button
        state (enabled or disabled) to prevent invalid operations (e.g.,
        merging a single PDF without compression). Triggers a UI update
        after the state change.
        """
        file_paths = self.main_panel.filebox.all_rows
        file_num = len(file_paths)
        need_compress = self.settings_panel.compress_selector.get()

        merge_btn = self.btns_panel.ui.get("btn_merge")
        if not merge_btn:
            return

        if file_num == 1:
            suffix = file_paths[0].suffix.lower()

            if suffix == ".pdf":
                self.btns_panel.app_mode = (
                    App_Mode.COMPRESS if need_compress else App_Mode.MERGE
                )
            else:
                self.btns_panel.app_mode = App_Mode.CONVERT
        else:
            self.btns_panel.app_mode = App_Mode.MERGE

        is_invalid_state = (
            file_num == 1
            and file_paths[0].suffix.lower() == ".pdf"
            and not need_compress
        )

        merge_btn.configure(state="disabled" if is_invalid_state else "normal")

        self.btns_panel.update_conditional_button()

    @update_ui_after("_update_merge_button")
    def add_files(self):
        self.main_panel.add_files()

    @update_ui_after("_update_merge_button")
    def remove_files(self):
        self.main_panel.remove_files()

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
            confirmed = ConfirmDialog.ask(
                parent=self,
                scenario_key="confirmation.confirm_update",
                scrollable_content=True,
                version=result.release.version,
                changelog_text=result.release.notes,
            )
            if confirmed:
                webbrowser.open_new_tab(config.RELEASES_URL)
                return
        else:
            current_v = self.version_controller._get_current_version()
            self.notifier.info(scenario_key="no_updates", version=current_v)

    def show_about(self) -> None:
        """Gather application metadata and display the About dialog."""
        current_version = self.version_controller._get_current_version()
        engine_class = getattr(self.conversion_service.converter, "__class__", None)
        engine_name = engine_class.__name__ if engine_class else "Unknown"
        AboutDialog(self, current_version, engine_name)

    def get_text_from_file(self, *, file_path: Path) -> str | None:
        """
        Read and return the content of a text file, triggering a notification on failure.

        Attempts to read the provided file using the FileToolKit. If the file is
        missing or an error occurs during reading, it logs the exception and
        notifies the user via the internal notification system using the
        appropriate error scenario.

        Args:
            file_path (Path): The filesystem path to the text file to be read.

        Returns:
            str | None: The content of the file if successful; None if an error occurred.
        """
        try:
            raw_text = FileToolKit.read_text_file(file_path=file_path)
            return raw_text
        except FileNotFoundError:
            logger.error(f"File not found by {file_path}")
            self.notifier.error(
                scenario_key="file_not_found_error",
                file_name=file_path,
            )
        except Exception as e:
            logger.error(f"Error reading license file: {e}")
            self.notifier.error(
                scenario_key="file_read_error",
                path=file_path,
            )

    def show_text_content(
        self, *, text: str, scenario_key: str, win_size: str = "750x600"
    ) -> None:
        """Build and grid UI button panels; return map of widget instances."""
        self.notifier.info(
            text=text,
            scenario_key=scenario_key,
            font_size=14,
            size=win_size,
            app_name=config.APP_NAME,
            with_footer=False,
        )

    def show_dependencies(self):
        """Load and display dependency information in a modal window."""
        dep_path = Path(config.DEPENDENCIES_PATH)
        dep_text = self.get_text_from_file(file_path=dep_path)
        if dep_text:
            self.show_text_content(
                text=dep_text, scenario_key="dependencies_info", win_size="900x600"
            )

    def show_license(self) -> None:
        """Display the license text in the notification dialog."""
        license_path = Path(config.LICENCE_PATH)
        cur_year = datetime.now().year
        license_text = self.get_text_from_file(file_path=license_path)

        self.notifier.info(
            text=license_text,
            scenario_key="license_info",
            font_size=14,
            size="750x600",
            year=cur_year,
            app_name=config.APP_NAME,
            with_footer=True,
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

    def schedule_ui_task(self, func, *args, delay: int = 10, **kwargs):
        if threading.current_thread() != threading.main_thread():
            self.after(delay, lambda: func(*args, **kwargs))
        else:
            func(*args, **kwargs)

    def save_result(
        self,
        *,
        data: bytes,
        output_path: str,
        stage: str = "saving",
        reset_ui_on_error: bool = True,
    ):
        """Save bytes to file, manage progress callbacks, and handle saving errors."""
        try:
            self.callback.safe_callback("progress", stage=stage, mode="indeterminate")

            FileToolKit.write_bytes(bytes_data=data, file_path=Path(output_path))

            self.callback.safe_callback(
                "progress", stage="common", mode="determinate", current=1, total=1
            )
            self.callback.safe_callback(
                "status", key=f"{stage}.done", status="info", path=output_path
            )

        except OSError as e:
            logger.error(
                f"Saving stage ({stage}) failed (OS Error): {e}", exc_info=True
            )
            if reset_ui_on_error:
                self.schedule_ui_task(self.main_panel.progress_bar_reset)
            self.callback.safe_callback(
                "status",
                key=f"{stage}.error.permission",
                status="error",
                path=Path(output_path).name,
            )

        except Exception as e:
            logger.error(
                f"Saving stage ({stage}) failed (Unknown Error): {e}", exc_info=True
            )
            if reset_ui_on_error:
                self.schedule_ui_task(self.main_panel.progress_bar_reset)
            self.callback.safe_callback(
                "status", key=f"{stage}.error.unknown", status="error"
            )

    def _get_page_format(self) -> PageFormat | None:
        """Retrieve and return the selected page format configuration."""
        page_format_name = self.settings_panel.get_widget_value(
            widget_id="format_selector"
        )
        return config.PAGE_FORMATS.get(page_format_name, None)

    @threaded_task
    def _run_merge_worker(
        self, files: List[tuple[int, Path]], output_path: str
    ) -> None:
        """Merge the selected files, optionally compress the result, and save it."""

        self.schedule_ui_task(self.main_panel.progress_bar_reset)
        self.callback.safe_callback(
            "progress",
            **{
                "stage": "analyzing",
                "mode": "indeterminate",
            },
        )
        try:
            conversion_res = self.conversion_service.get_pdfs_data(files=files)
            target_format = self._get_page_format()
            data = self.merger.merge_to_pdf(
                conversion_rep=conversion_res, target_page_format=target_format
            )
            need_compress: bool = self.settings_panel.compress_selector.get()
            if need_compress:
                data = self.compressor.compress(pdf_bytes=data)
            if data:
                self.save_result(data=data, output_path=output_path)
        except InterruptedError:
            self.callback.safe_callback(
                "status",
                **{
                    "key": "processing.cancel",
                    "status": "info",
                },
            )
            self.schedule_ui_task(self.main_panel.progress_bar_reset, delay=10)
            return
        except Exception as e:
            logger.error(f"Merge stage failed: {e}", exc_info=True)
            self.schedule_ui_task(self.main_panel.progress_bar_reset)
            return

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
        PAGE_LIMIT=10000
        try:
            pages = get_selected_pages(raw=raw_input.strip(),page_limit=PAGE_LIMIT)
            self.page_extractor.validate_pages(
                input_path=Path(input_path), pages_to_extract=pages
            )
        except InvalidPageInputError:
            self.notifier.warning(scenario_key="wrong_page_format")
            return
        except PageLimitExceededError as e:
            self.notifier.error(
                scenario_key="page_limit_error",
                limit=PAGE_LIMIT,
            )
            return
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

    @threaded_task
    def _run_page_extractor_worker(
        self, *, input_path: str, pages: List[int], output_path: str
    ) -> None:
        """Run the page-extraction worker and report progress or errors."""
        try:
            self.schedule_ui_task(self.main_panel.progress_bar_reset)
            data = self.page_extractor.extract_pages(
                input_path=input_path,
                pages_to_extract=pages,
                output_path=output_path,
            )
            need_compress: bool = self.settings_panel.compress_selector.get()
            if need_compress:
                data = self.compressor.compress(pdf_bytes=data)
            if data:
                self.save_result(data=data, output_path=output_path)
        except InterruptedError:
            self.callback.safe_callback(
                "status",
                **{
                    "key": "processing.cancel",
                    "status": "info",
                },
            )
            self.schedule_ui_task(self.main_panel.progress_bar_reset, delay=10)
            return
        except Exception as e:
            error_msg = f"Error during page extraction: {e}"
            if isinstance(e, ValueError):
                self.schedule_ui_task(
                    lambda: self.notifier.error(
                        scenario_key="page_extraction_error",
                        file_name=input_path,
                    ),
                    delay=10,
                )
            else:
                self.callback.set_status(key="extract.error", status="error", error=e)
                logger.error(error_msg, exc_info=True)
                self.schedule_ui_task(self.main_panel.progress_bar_reset, delay=10)
            return

    def _on_closing(self) -> None:
        """Handle window close requests and wait for background work if needed."""
        self._manage_services(action="stop")
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self._wait_for_thread_finish()

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

    def _manage_services(self, *, action: Literal["stop", "reset"]):
        for service in [
            self.merger,
            self.compressor,
            self.conversion_service.converter,
            self.page_extractor,
        ]:
            if service and hasattr(service, "stop_event"):
                match action:
                    case "stop":
                        service.stop_event.set()
                    case "reset":
                        service.stop_event.clear()

    def _save_and_destroy(self) -> None:
        """Persist current settings and destroy the main window."""
        settings: Dict[str, str] = self.settings_panel.collect_data()
        self.settings_manager.save_settings(settings=settings)
        self.destroy()
