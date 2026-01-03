from pathlib import Path
from pypdf import PdfReader, PdfWriter
import logging
logger = logging.getLogger(__name__)


class PdfSpliter:

    def extract_pages(self ,*, input_path: str, pages_to_extract: list[int], output_path: str | Path) -> None:

        input_file = Path(input_path)
        output_file = Path(output_path)

        # Load PDF
        writer = PdfWriter()
        with input_file.open("rb") as f:
            reader = PdfReader(f)

            if not pages_to_extract:
                raise ValueError("No valid pages to extract")

            # Add pages
            for p in pages_to_extract:
                writer.add_page(reader.pages[p])

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save output
        with output_file.open("wb") as f:
            writer.write(f)

        logger.info(f"📁 Extracted pages saved to: {output_file}")
        return output_file
