from pathlib import Path
from pypdf import PdfReader, PdfWriter
import logging

logger = logging.getLogger(__name__)

class PageExtractor:

    def extract_pages(self, *, input_path: str, pages_to_extract: list[int], output_path: str | Path, callback: callable = None) -> Path:
        input_file = Path(input_path)
        output_file = Path(output_path)
        progress_bar_mode: str = "determinate"
        stage_name: str = "Extracting pages"

        writer = PdfWriter()
        with input_file.open("rb") as f:
            reader = PdfReader(f)
            self._validate_pages(reader = reader, pages = pages_to_extract)
            total_to_extract = len(pages_to_extract)
            
            # Get enumerated pages and add to writer

            for i, p in enumerate(pages_to_extract, 1):
                writer.add_page(reader.pages[p])
            
                if callback:
                    callback(
                        stage = stage_name, 
                        progress_bar_mode = progress_bar_mode,
                        current = i, 
                        total = total_to_extract, 
                        status_message = f"Processing page {p + 1} ({i}/{total_to_extract})..."
                    )

        # Create folder and save
        output_file.parent.mkdir(parents = True, exist_ok = True)
        with output_file.open("wb") as f:
            writer.write(f)
        return output_file
    
    def _validate_pages(self,*, reader: PdfReader, pages: list[int]) -> None:

        """Check if all specified pages exist in the file."""

        actual_total = len(reader.pages)

        # Find invalid indices
        invalid = [p + 1 for p in pages if p < 0 or p >= actual_total]
    
        if invalid:
            # Raise an exception with a detailed description
            # This will stop execution and give a clear understanding of what went wrong
            logger.debug(f"Invalid page numbers requested: {invalid} out of {actual_total} pages.")
            raise ValueError(
                f"Invalid page numbers: {invalid}. "
                f"The document only has {actual_total} pages."
            )
    