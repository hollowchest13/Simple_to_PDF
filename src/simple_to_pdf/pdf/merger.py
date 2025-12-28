from pypdf import PdfReader,PdfWriter
from pathlib import Path
from ..converters import get_converter
import io
class PdfMerger:
    def __init__(self):
        self.converter = get_converter()

    def merge_to_pdf(self,*, files: list[tuple[int, str]], output_path: str | Path) -> Path:
        pdfs: list[tuple[int, bytes]] = []
        pdfs.extend(self.converter.convert_to_pdf(files = files))
        writer = PdfWriter()
    
        # Сортуємо список за індексом
        pdfs_sorted = sorted(pdfs, key = lambda x: x[0])
        for idx,pdf_bytes in pdfs_sorted:
            try:
                reader=PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                print(f"⚠️ [{idx}] Warning: failed to read PDF ({e})")
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True,exist_ok=True)

        with output_file.open("wb") as f:
            writer.write(f)
        
        print(f"📁 Merged PDF saved to: {output_file}")
        return output_file
