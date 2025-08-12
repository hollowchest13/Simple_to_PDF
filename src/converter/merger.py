from pypdf import PdfReader, PdfWriter
from pathlib import Path
import os

class PdfManager:

    def __init__(self):
        self.pdf_list = []

    # Merge multiple PDFs into a single PDF file
    def merge_pdfs(self,*,pdfs: list[str], output_path: str) -> str:
        
        writer = PdfWriter()

        for path in pdfs:
            if os.path.exists(path) and path.lower().endswith('.pdf'):
                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)
                print(f"✅ Added: {path}")
            else:
                print(f"⚠️ Warning: {path} does not exist or is not a .pdf file.")

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"📁 Merged PDF saved to: {output_path}")
        return output_path
    
    # Remove pages from a PDF file
    def extract_pages(self, *, input_path: tuple[str], pages_to_extract: list[int], output_path: str) -> None:
        writer = PdfWriter()
        with open(input_path[0], "rb") as f:
            print(input_path[0])
            reader = PdfReader(f)
            total_pages = len(reader.pages)

            # Normalize page numbers to 0-based index and filter invalid entries

            if not pages_to_extract:
                raise ValueError("No valid pages to extract")

            # Add pages in the order specified, allowing duplicates
            for p in pages_to_extract:
                writer.add_page(reader.pages[p])

            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the new PDF file
        with open(output_path, "wb") as f:
            writer.write(f)

