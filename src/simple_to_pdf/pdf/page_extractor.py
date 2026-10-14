import logging
from collections.abc import Callable
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from simple_to_pdf.base_services.base import BaseService
from simple_to_pdf.utils.file_tools import get_unique_path

logger = logging.getLogger(__name__)


class PageExtractor(BaseService):
    def __init__(self):
        super().__init__()
        self.callback = None

    @property
    def callback(self) -> Callable:
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    def extract_pages(
        self,
        *,
        input_file: Path,
        pages_to_extract: list[int],
        output_file: Path,
    ) -> Path:
        stage_name = "extracting"

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
                            stage=stage_name,
                            mode="determinate",
                            current=i,
                            total=total,
                            filename=f"page {p_num}",
                        )
                    except IndexError as e:
                        logger.error(f"Page {p_num} is out of range for {input_file}")
                        self.callback(
                            "status",
                            key=f"{stage_name}.error",
                            status="error",
                            page_number=p_num,
                            error=e,
                        )
            output_file = get_unique_path(output_file)
            writer.write(output_file)

            self.callback(
                "status",
                key=f"{stage_name}.done",
                status="info",
                path=str(output_file),
            )
            return output_file

        except InterruptedError:
            logger.info(f"{stage_name} successfully cancelled by the user.")
            raise

        finally:
            writer.close()

    def validate_pages(
        self,
        *,
        input_path: Path,
        pages_to_extract: list[int] | None,
    ) -> None:
        """
        Validates if the provided page numbers exist within the source PDF.
        Raises ValueError if indices are out of bounds or list is empty.
        """
        if not pages_to_extract:
            raise ValueError("No pages selected for extraction.")
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
