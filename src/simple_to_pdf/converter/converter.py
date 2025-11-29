import win32com.client as win32
from pathlib import Path
import tempfile
import os

import win32com.client as win32
from pathlib import Path
import tempfile
import os

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
               
    
    def covert_word_to_pdf(self,*,input_file : str)->Path:
         pass