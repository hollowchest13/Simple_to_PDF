import io
import logging
from pathlib import Path
from typing import Callable

from pypdf import PdfReader, PdfWriter

from simple_to_pdf.base_services.base import BaseService

logger = logging.getLogger(__name__)


class PageExtractor(BaseService):
    def __init__(self):
        self._callback: Callable = lambda *args, **kwargs: None

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    def extract_pages(
        self,
        *,
        input_path: str,
        pages_to_extract: list[int],
        output_path: str | Path,
    ) -> bytes:
        input_file = Path(input_path)
        output_file = Path(output_path).resolve()
        stage = "extracting"

        writer = PdfWriter()

        try:
            with input_file.open("rb") as f:
                reader = PdfReader(f)
                total = len(pages_to_extract)

                for i, p_num in enumerate(pages_to_extract, 1):
                    self.check_stop()

                    p_idx = p_num - 1
                    try:
                        writer.add_page(reader.pages[p_idx])
                        self.callback(
                            "progress",
                            **{
                                "stage": stage,
                                "mode": "determinate",
                                "current": i,
                                "total": total,
                                "filename": f"page {p_num}",
                            },
                        )
                    except IndexError as e:
                        logger.error(f"Page {p_num} is out of range for {input_path}")
                        self.callback(
                            "status",
                            **{
                                "key": f"{stage}.error",
                                "status": "error",
                                "page_number": p_num,
                                "error": e,
                            },
                        )
            with io.BytesIO() as buffer:
                writer.write(buffer)
                data = buffer.getvalue()

            self.callback(
                "status",
                **{
                    "key": f"{stage}.done",
                    "status": "info",
                    "path": str(output_file),
                },
            )
            return data

        except InterruptedError:
            self.callback(
                "status",
                **{
                    "key": f"{stage}.canceled",
                    "status": "info",
                },
            )
            return b""

        finally:
            writer.close()

    def validate_pages(
        self,
        *,
        input_path: Path,
        pages_to_extract: list[int],
    ) -> None:
        """
        Validates if the provided page numbers exist within the source PDF.
        Raises ValueError if indices are out of bounds or list is empty.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        with open(input_path, "rb") as f:
            reader = PdfReader(f)
            actual_total = len(reader.pages)

        invalid = [
            p_num + 1 for p_num in pages_to_extract if p_num < 1 or p_num > actual_total
        ]

        if invalid:
            raise ValueError(
                f"Invalid page numbers: {invalid}. File has only {actual_total} pages."
            )

        if not pages_to_extract:
            raise ValueError("No pages selected for extraction.")
