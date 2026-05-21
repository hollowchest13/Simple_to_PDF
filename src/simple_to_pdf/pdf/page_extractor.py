import logging
from pathlib import Path
from typing import Callable

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


class PageExtractor:
    def __init__(self):
        self._callback=lambda *args,**kwargs:None
    
    @property
    def callback(self):
        return self._callback
    
    @callback.setter
    def callback(self,value):
        self._callback=value if not value is None else lambda *args,**kwargs:None

    def extract_pages(
        self,
        *,
        input_path: str,
        pages_to_extract: list[int],
        output_path: str | Path,
        callback: Callable | None = None,
    ) -> Path:
        """
        Extracts specific pages from a PDF file and saves them to a new file.
        Provides progress updates via the callback.
        """
        input_file = Path(input_path)
        output_file = Path(output_path).resolve()

        writer = PdfWriter()

        # Step 1: Read the source file and extract pages
        with input_file.open("rb") as f:
            reader = PdfReader(f)
            total = len(pages_to_extract)

            # Initial callback to set up progress bar
            if callback:
                callback(
                    "progress",
                    **{
                        "stage": "extracting",
                        "mode": "determinate",
                        "current": 0,
                        "total": total,
                    },
                )

            for i, p_num in enumerate(pages_to_extract, 1):
                p_idx = p_num - 1
                try:
                    writer.add_page(reader.pages[p_idx])
                except IndexError as e:
                    logger.error(f"Page {p_num} is out of range for {input_path}")
                    if callback:
                        callback(
                            "status",
                            **{
                                "key": "extract.error",
                                "status": "error",
                                "page_number": p_num,
                                "error": e,
                            },  # Display 1-based index for user
                        )
                    continue

                # Update progress for every page processed
                if callback:
                    callback(
                        "progress",
                        **{
                            "stage": "extracting",
                            "mode": "determinate",
                            "current": i,
                            "total": total,
                            "filename": f"page {p_num}",
                        },  # Display 1-based index for user
                    )

        # Step 2: Ensure output directory exists and write the file
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("wb") as f:
            writer.write(f)

        # Step 3: Final status update
        if callback:
            callback(
                "status",
                **{
                    "key": "extract.done",
                    "status": "info",
                    "path": str(output_file),
                },
            )

        return output_file

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

        # Check for indices that are negative or exceed the actual page count
        invalid = [
            p_num + 1 for p_num in pages_to_extract if p_num < 1 or p_num > actual_total
        ]

        if invalid:
            raise ValueError(
                f"Invalid page numbers: {invalid}. File has only {actual_total} pages."
            )

        if not pages_to_extract:
            raise ValueError("No pages selected for extraction.")
