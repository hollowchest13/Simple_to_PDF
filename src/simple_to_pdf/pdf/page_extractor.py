import logging
from pathlib import Path

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


class PageExtractor:
    def extract_pages(
        self,
        *,
        input_path: str,
        pages_to_extract: list[int],
        output_path: str | Path,
        callback: callable = None,
    ) -> Path:
        input_file = Path(input_path)
        output_file = Path(output_path)
        progress_bar_mode: str = "determinate"
        stage_name: str = "Extracting pages"

        writer = PdfWriter()
        with input_file.open("rb") as f:
            reader = PdfReader(f)
            total_to_extract = len(pages_to_extract)

            # Get enumerated pages and add to writer

            for i, p in enumerate(pages_to_extract, 1):
                writer.add_page(reader.pages[p])

                if callback:
                    callback(
                        stage=stage_name,
                        progress_bar_mode=progress_bar_mode,
                        current=i,
                        total=total_to_extract,
                        status_message=f"Processing page {p + 1} ({i}/{total_to_extract})...",
                    )

        # Create folder and save
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("wb") as f:
            writer.write(f)
        return output_file

    def validate_pages(self, *, input_path: Path, pages_to_extract: list[int]) -> None:
        """Check if all specified pages exist in the file."""

        with open(input_path, "rb") as f:
            reader = PdfReader(f)
            actual_total = len(reader.pages)

        invalid = [p + 1 for p in pages_to_extract if p < 0 or p >= actual_total]

        if invalid:
            raise ValueError(
                f"Invalid page numbers file has only {actual_total} pages."
            )

        if not pages_to_extract:
            raise ValueError("No pages selected for extraction.")
