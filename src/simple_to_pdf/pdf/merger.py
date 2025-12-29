from pypdf import PdfReader,PdfWriter
from pathlib import Path
from ..converters import get_converter
import io
class PdfMerger:
    def __init__(self):
        self.converter = get_converter()

    def merge_to_pdf(self, *, files: list[tuple[int, str]], output_path: str | Path, callback = None) -> Path:

        """Merges multiple files into a single PDF."""

        # 1. Convertation
        pdfs: list[tuple[int, bytes]] = []
        pdfs.extend(self.converter.convert_to_pdf(files = files))
    
        writer = PdfWriter()
        pdfs_sorted = sorted(pdfs, key=lambda x: x[0])
        total = len(pdfs_sorted)

        # 2. Base cycle of merging
        for i, (idx, pdf_bytes) in enumerate(pdfs_sorted, 1):
            try:
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
                # If GUI gives us a function to update progress, we call it
                if callback:
                    # We pass current, total and filename
                    # (Since there's no filename here, we can just use index or "File X")
                    callback(current = i, total = total, filename = f"Document {idx}")
            except Exception as e:
                print(f"⚠️ [{idx}] Warning: failed to read PDF ({e})")

        # 3. Saving the result
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents = True, exist_ok = True)

        with output_file.open("wb") as f:
            writer.write(f)
        return output_file
