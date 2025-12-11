from pypdf import PdfReader,PdfWriter
from pathlib import Path
from src.simple_to_pdf.converter import PdfConverter
import io
class PdfMerger:
    def __init__(self):
        self.converter=PdfConverter()

    def is_pdf_file(self,*, file_path :Path)->bool:
        return file_path.suffix.lower() == ".pdf"
        
    def is_excel_file(self,*, file_path: Path) -> bool:
         return file_path.suffix.lower() in {".xls", ".xlsx"}
           
    def is_image_file(self,*, file_path:Path)->bool:
        return file_path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    
    def is_word_file(self,*, file_path: Path) -> bool:
        return file_path.suffix.lower() in {".doc", ".docx"}
        
    def get_pdf_list(self,*, files: list[tuple[int, str]]) -> list[tuple[int, bytes]]:

        exls: list[tuple[int,Path]] = []
        wrds: list[tuple[int,Path]] = []
        pdfs: list[tuple[int, bytes]] = []
        converted: list[tuple[int, bytes]] = []

        for idx, path_str in files:
            path = Path(path_str)
            if path.exists():
                if self.is_pdf_file(file_path = path):
                     pdfs.append((idx,path.read_bytes()))
                elif self.is_excel_file(file_path = path):
                    exls.append((idx,path))
                elif self.is_word_file(file_path = path):
                    wrds.append((idx,path))

        converted.extend(self.converter.convert_excel_to_pdf(files = exls))
        converted.extend(self.converter.convert_word_to_pdf(files = wrds))
        pdfs.extend(converted)
        return pdfs

    def merge_to_pdf(self,*, files: list[tuple[int, str]], output_path: str | Path) -> Path:
        pdfs: list[tuple[int, bytes]] = []
        pdfs.extend(self.get_pdf_list(files = files))
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
        output_file=Path(output_path).resolve()
        output_file.parent.mkdir(parents=True,exist_ok=True)

        with output_file.open("wb") as f:
            writer.write(f)
        
        print(f"📁 Merged PDF saved to: {output_file}")
        return output_file
