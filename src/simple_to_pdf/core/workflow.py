import logging
import multiprocessing as mp
import tempfile
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Literal

from simple_to_pdf.pdf import ConversionService, PageExtractor, PDFCompressor, PdfMerger
from simple_to_pdf.pdf.models import PageFormat
from simple_to_pdf.utils.process_tools import (
    execute_in_process,
)

logger = logging.getLogger(__name__)


class WorkflowManager:
    def __init__(
        self,
        conversion_service: ConversionService | None = None,
        merger_service: PdfMerger | None = None,
        compressor_service: PDFCompressor | None = None,
        page_extractor_service: PageExtractor | None = None,
    ):
        self.workers = 2
        self.process_executor = ProcessPoolExecutor(max_workers=self.workers)
        self.mp_manager = mp.Manager()
        self.mp_queue = self.mp_manager.Queue()
        self.converter = conversion_service or ConversionService()
        self.merger = merger_service or PdfMerger()
        self.compressor = compressor_service or PDFCompressor()
        self.extractor = page_extractor_service or PageExtractor()
        self.services = [
            self.merger,
            self.compressor,
            self.converter,
            self.extractor,
        ]
        self._callback = lambda *args, **kwargs: None

        # Управління процесами для швидкого скасування
        self._executor = None

    @property
    def callback(self) -> Callable:
        return self._callback

    def merge_files(
        self,
        files: list[tuple[int, Path]],
        output_path: Path,
        need_compress: bool,
        target_format: PageFormat | None,
    ) -> None:
        """Merge the selected files, optionally compress the result, and save it."""
        self.callback(
            "progress",
            stage="analyzing",
            mode="indeterminate",
        )

        try:
            with tempfile.TemporaryDirectory() as tmp_dir_str:
                tmp_dir = Path(tmp_dir_str)
                conversion_res = self.converter.get_conversion_rep(
                    files=files, out_dir=tmp_dir
                )

                if self._is_cancelled():
                    raise InterruptedError()

                self.callback("progress", stage="merging", mode="indeterminate")
                data: bytes = execute_in_process(
                    executor=self._get_executor(),
                    mp_queue=self.mp_queue,
                    ui_callback=self.callback,
                    service_cls=PdfMerger,
                    method_name="merge_to_pdf",
                    method_kwargs={
                        "conversion_rep": conversion_res,
                        "target_page_format": target_format,
                        "outout_path": output_path,
                    },
                )

                if self._is_cancelled():
                    raise InterruptedError()

                if need_compress and data:
                    self.callback("progress", stage="compressing", mode="indeterminate")
                    data = execute_in_process(
                        executor=self._get_executor(),
                        mp_queue=self.mp_queue,
                        ui_callback=self.callback,
                        service_cls=PDFCompressor,
                        method_name="compress",
                        method_kwargs={"pdf_bytes": data},
                    )

                if self._is_cancelled():
                    raise InterruptedError()

        except InterruptedError:
            self.callback(
                "status",
                key="processing.cancel",
                status="info",
            )
        except Exception:
            logger.exception("Merge stage failed!")
            self.callback(
                "status",
                key="processing.error",
                status="error",
            )
        finally:
            self.schedule_ui_task(self.main_panel.progress_bar_reset)

    def _is_cancelled(self) -> bool:
        """Checks whether a cancellation or stop signal has been issued."""

        for service in self.services:
            if (
                service
                and hasattr(service, "stop_event")
                and service.stop_event.is_set()
            ):
                return True
        return False

    def kill_executor(self) -> None:
        """Force terminate background process pool and underlying child processes."""
        if self.process_executor is None:
            return

        try:
            processes = getattr(self.process_executor, "_processes", {}) or {}

            if isinstance(processes, dict):
                for pid, process in list(processes.items()):
                    if process and process.is_alive():
                        process.terminate()

            self.process_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            logger.exception("Error while killing process executor!")
        finally:
            self.process_executor = None

    def _get_executor(self) -> ProcessPoolExecutor:
        """Returns an active ProcessPoolExecutor, creating a new one if needed."""
        if self.process_executor is None or getattr(
            self.process_executor, "_shutdown", False
        ):
            self.process_executor = ProcessPoolExecutor(max_workers=self.workers)
        return self.process_executor

    def close_mp_manager(self) -> None:
        """Shutdown the multiprocessing manager to release process resources."""
        if hasattr(self, "mp_manager") and self.mp_manager:
            try:
                self.mp_manager.shutdown()
            except Exception:
                logger.exception("Shutdown multiprocessing error!")

    def manage_services(self, *, action: Literal["stop", "reset"]):
        for service in self.services:
            if service and hasattr(service, "stop_event"):
                match action:
                    case "stop":
                        service.stop_event.set()
                    case "reset":
                        service.stop_event.clear()

    def page_extraction(
        self, *, input_path: str, pages: list[int], output_path: Path
    ) -> None:
        """Run the page-extraction worker and report progress or errors."""
        try:
            self.schedule_ui_task(self.main_panel.progress_bar_reset)
            data: bytes = execute_in_process(
                executor=self._get_executor(),
                mp_queue=self.mp_queue,
                ui_callback=self.callback,
                service_cls=PageExtractor,
                method_name="extract_pages",
                method_kwargs={
                    "input_file": input_path,
                    "pages_to_extract": pages,
                    "output_file": output_path,
                },
            )
            need_compress: bool = self.settings_panel.compress_selector.get()
            if need_compress:
                self.callback("progress", stage="compressing", mode="indeterminate")
                data = execute_in_process(
                    executor=self._get_executor(),
                    mp_queue=self.mp_queue,
                    ui_callback=self.callback,
                    service_cls=PDFCompressor,
                    method_name="compress",
                    method_kwargs={"pdf_bytes": data},
                )
        except InterruptedError:
            self.callback(
                "status",
                key="processing.cancel",
                status="info",
            )
            self.schedule_ui_task(self.main_panel.progress_bar_reset)
            return
        except Exception as e:
            error_msg = f"Error during page extraction: {e}"
            if isinstance(e, ValueError):
                self.schedule_ui_task(
                    lambda: self.notifier.error(
                        scenario_key="page_extraction_error",
                        file_name=input_path,
                    ),
                )
            else:
                self.callback("status", key="extract.error", status="error", error=e)
                logger.exception(error_msg)
                self.schedule_ui_task(self.main_panel.progress_bar_reset)
            return
