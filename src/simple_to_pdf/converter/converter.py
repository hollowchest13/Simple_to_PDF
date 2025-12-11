import win32com.client as win32
from pathlib import Path
import tempfile
from PIL import Image
import io


class PdfConverter:
    def __init__(self):
        self.pdf_files: list[tuple[int, Path]] = []
        
    def convert_excel_to_pdf(self, *, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False

        results = []
        try:
            for idx, f in files:
                input_file = Path(f).resolve()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    temp_pdf_path = Path(tmp.name)

                wb = None
                try:
                    wb = excel.Workbooks.Open(str(input_file))
                    wb.ExportAsFixedFormat(0, str(temp_pdf_path))

                    if temp_pdf_path.exists():
                        pdf_bytes = temp_pdf_path.read_bytes()
                        results.append((idx, pdf_bytes))
                finally:
                    if wb is not None:
                        wb.Close(SaveChanges=False)
                    if temp_pdf_path.exists():
                        temp_pdf_path.unlink()
        finally:
            excel.Quit()
            del excel
        return results
               
    
    def convert_word_to_pdf(self, *, word_files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
         word = win32.Dispatch("Word.Application")
         word.Visible = False

         results = []
         try:
             for idx, wf in word_files:
                input_file = Path(wf).resolve()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    temp_pdf_path = Path(tmp.name)

                doc = None
                try:
                    doc = word.Documents.Open(str(input_file))
                    doc.ExportAsFixedFormat(0, str(temp_pdf_path))

                    if temp_pdf_path.exists():
                        pdf_bytes = temp_pdf_path.read_bytes()
                        results.append((idx, pdf_bytes))
                finally:
                    if doc is not None:
                        doc.Close(SaveChanges=False)
                    if temp_pdf_path.exists():
                        temp_pdf_path.unlink()
         finally:
            word.Quit()
            del word
         return results
    
    def convert_images_to_pdf(self,*, files: list[tuple[int,str]])->list[tuple[int, bytes]]:
        pdfs: list[tuple[int,bytes]] = []
        for idx,path_str in files:
            path=Path(path_str)
            if path.exists():
                try:
                    img=Image.open(path).convert("RGB")
                    buffer=io.BytesIO()
                    img.save(buffer,format="PDF")
                    pdfs.append((idx,buffer.getvalue()))
                except Exception as e:
                     print(f"⚠️ [{idx}] Warning: failed to convert image {path} ({e})")
                else:
                    print(f"⚠️ [{idx}] Skipped: {path} (not an image or missing)")

        return pdfs



                
               
    

