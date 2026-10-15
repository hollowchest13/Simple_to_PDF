import logging
import multiprocessing as mp
import queue
import shutil
import tempfile
import time
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from pathlib import Path
from typing import Any, Literal, TypeVar

from simple_to_pdf.pdf import ConversionService, PageExtractor, PDFCompressor, PdfMerger
from simple_to_pdf.pdf.models import PageFormat
from simple_to_pdf.utils.process_tools import (
    run_service_method_in_process,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


class WorkflowManager:
    def __init__(
        self,
        conversion_service: ConversionService | None = None,
        merger_service: PdfMerger | None = None,
        compressor_service: PDFCompressor | None = None,
        page_extractor_service: PageExtractor | None = None,
    ):
        self._workers = 2
        self._process_executor: ProcessPoolExecutor | None = ProcessPoolExecutor(
            max_workers=self._workers
        )
        self._mp_manager = mp.Manager()
        self._mp_queue = self._mp_manager.Queue()
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

    @property
    def callback(self) -> Callable:
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    def merge_files(
        self,
        *,
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
                merged_pdf_path: Path = self.execute_in_process(
                    ui_callback=self.callback,
                    service_cls=PdfMerger,
                    method_name="merge_to_pdf",
                    method_kwargs={
                        "conversion_rep": conversion_res,
                        "target_page_format": target_format,
                        "output_path": tmp_dir / "merged.pdf",
                    },
                )

                if self._is_cancelled():
                    raise InterruptedError()
                compressed_pdf_path = tmp_dir / "compressed.pdf"
                if need_compress and merged_pdf_path:
                    self.callback("progress", stage="compressing", mode="indeterminate")
                    merged_pdf_path = self.execute_in_process(
                        ui_callback=self.callback,
                        service_cls=PDFCompressor,
                        method_name="compress",
                        method_kwargs={
                            "input_pdf_path": merged_pdf_path,
                            "output_path": compressed_pdf_path,
                        },
                    )

                shutil.move(compressed_pdf_path, output_path)
                self.callback(
                    "status", key="saving.done", status="info", path=output_path
                )
                if self._is_cancelled():
                    raise InterruptedError()

        except InterruptedError:
            logger.warning("File merge canceled by user!")
            raise
        except Exception:
            logger.exception("Merge stage failed!")
            raise

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
        if self._process_executor is None:
            return

        try:
            processes = getattr(self._process_executor, "_processes", {}) or {}

            if isinstance(processes, dict):
                for _, process in list(processes.items()):
                    if process and process.is_alive():
                        process.terminate()

            self._process_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            logger.exception("Error while killing process executor!")
        finally:
            self._process_executor = None

    def _get_executor(self) -> ProcessPoolExecutor:
        """Returns an active ProcessPoolExecutor, creating a new one if needed."""
        if self._process_executor is None or getattr(
            self._process_executor, "_shutdown", False
        ):
            self._process_executor = ProcessPoolExecutor(max_workers=self._workers)
        return self._process_executor

    def close_mp_manager(self) -> None:
        """Shutdown the multiprocessing manager to release process resources."""
        if hasattr(self, "mp_manager") and self._mp_manager:
            try:
                self._mp_manager.shutdown()
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

    def extract_pages(
        self,
        *,
        input_path: Path,
        pages: list[int],
        output_path: Path,
        need_compress: bool,
    ) -> None:
        """Run the page-extraction worker and report progress or errors."""
        try:
            with tempfile.TemporaryDirectory() as tmp_dir_str:
                tmp_dir = Path(tmp_dir_str)
                extracted_pdf_path: Path = self.execute_in_process(
                    ui_callback=self.callback,
                    service_cls=PageExtractor,
                    method_name="extract_pages",
                    method_kwargs={
                        "input_file": input_path,
                        "pages_to_extract": pages,
                        "output_file": tmp_dir / "extracted.pdf",
                    },
                )

                if need_compress:
                    self.callback("progress", stage="compressing", mode="indeterminate")
                    extracted_pdf_path = self.execute_in_process(
                        ui_callback=self.callback,
                        service_cls=PDFCompressor,
                        method_name="compress",
                        method_kwargs={"input_pdf_path": extracted_pdf_path},
                    )
                shutil.move(extracted_pdf_path, output_path)
                self.callback(
                    "status", key="saving.done", status="info", path=output_path
                )

        except InterruptedError:
            logger.warning("Page extraction canceled by user!")
            raise
        except ValueError:
            raise
        except Exception as e:
            error_msg = f"Error during page extraction: {e}"
            logger.exception(error_msg)
            raise

    def execute_in_process(
        self,
        *,
        ui_callback: Any,
        service_cls: type[T],
        method_name: str,
        method_kwargs: dict[str, Any],
        callback_attr: str = "_show_callback",
        poll_interval: float = 0.02,
    ) -> Any:
        """
            Executed in a GUI background thread.
        Launches the task within the process and reads notifications from the `mp_queue` into the UI queue until completion.
        """
        if self._process_executor is None:
            self._process_executor = self._get_executor()
        try:
            future: Future[T] = self._process_executor.submit(
                run_service_method_in_process,
                service_cls=service_cls,
                method_name=method_name,
                method_kwargs=method_kwargs,
                mp_queue=self._mp_queue,
                callback_attr=callback_attr,
            )
        except RuntimeError as e:
            logger.warning(f"Failed to submit task to executor: {e}")
            raise InterruptedError("Process pool is no longer active.") from e

        # 1. Loop waiting for a Future to complete
        while not future.done():
            while not self._mp_queue.empty():
                try:
                    msg = self._mp_queue.get_nowait()
                    ui_callback(msg["event_type"], **msg["params"])
                except queue.Empty:
                    break

            time.sleep(poll_interval)

        # 2. Read the remaining notifications from the queue after the process completes
        while not self._mp_queue.empty():
            try:
                msg = self._mp_queue.get_nowait()
                ui_callback(msg["event_type"], **msg["params"])
            except queue.Empty:
                break

        # 3. Return the result or raise an error if the process crashed
        return future.result()
