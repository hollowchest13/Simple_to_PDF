from pathlib import Path
from src.simple_to_pdf.converters.base_converter import BaseConverter
import tempfile
import win32com.client as win32
import logging

logger = logging.getLogger(__name__)

class MSOfficeConverter(BaseConverter):
    def __init__(self, chunk_size: int = 30):  # Додай цей параметр
        super().__init__()
        self.chunk_size = chunk_size

    def convert_to_pdf(self, *, files: list[tuple[int, str]]) -> list[tuple[int, bytes]]:
        exls: list[tuple[int, Path]] = []
        wrds: list[tuple[int, Path]] = []
        imgs: list[tuple[int, Path]] = []
        final_results: list[tuple[int, bytes]] = []

        for idx, path_str in files:
            path = Path(path_str)
            if not path.exists():
                continue
            if self.is_pdf_file(file_path=path):
                final_results.append((idx, path.read_bytes()))
            elif self.is_excel_file(file_path=path):
                exls.append((idx, path))
            elif self.is_word_file(file_path=path):
                wrds.append((idx, path))
            elif self.is_image_file(file_path=path):
                imgs.append((idx, path))

        if exls:
            final_results.extend(self._convert_excel_to_pdf(files = exls))
        if wrds:
            final_results.extend(self._convert_word_to_pdf(word_files = wrds))
        if imgs:
            final_results.extend(self.convert_images_to_pdf(files = imgs))

        final_results.sort(key=lambda x: x[0])
        return final_results
    
    def _convert_excel_to_pdf(self, *, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        all_results = []
        
        # split for chunks
        for chunk in self.make_chunks(files, n = self.chunk_size):
            all_results.extend(self._process_excel_chunk(chunk))
        
        return all_results

    def _process_excel_chunk(self, chunk: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        results = []
        # Run Excel only for this chunk
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False # Disable alerts to prevent pop-ups

        try:
            for idx, f in chunk:
                pdf_data = self._convert_single_excel(excel, f)
                if pdf_data:
                    results.append((idx, pdf_data))
        finally:
            excel.Quit() #Close Excel process
            del excel
            
        return results
    
    def _prepare_excel_for_export(self, wb):

        """Setup printing options"""

        for sheet in wb.Sheets:
            width = sheet.UsedRange.Columns.Count
        
            # Налаштовуємо орієнтацію
            sheet.PageSetup.Orientation = 2 if width > 10 else 1
        
            # Налаштовуємо масштабування
            sheet.PageSetup.Zoom = False
            sheet.PageSetup.FitToPagesWide = 1
            sheet.PageSetup.FitToPagesTall = False

    def _convert_single_excel(self, excel_app, file_path: Path) -> bytes | None:

        """Converting a single file inside the opened application."""

        input_file = file_path.resolve()
        wb = None
        pdf_bytes = None
        
        with tempfile.NamedTemporaryFile(delete = False, suffix = ".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)
            
        try:
            wb = excel_app.Workbooks.Open(str(input_file), ReadOnly = True)
            self._prepare_excel_for_export(wb = wb)
            wb.ExportAsFixedFormat(0, str(temp_pdf_path))
            pdf_bytes = temp_pdf_path.read_bytes()
        except Exception as e:
            logger.error(f"❌  Excel file error in {file_path.name}: {e}", exc_info = True)
        finally:
            if wb:
                wb.Close(SaveChanges=False)
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
                
        return pdf_bytes
    
               
    def _convert_word_to_pdf(self, *, word_files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        all_results = []
        
        # Convert by chunks of 30 files
        for chunk in self.make_chunks(word_files, n=self.chunk_size):
            all_results.extend(self._process_word_chunk(chunk))
            
        return all_results

    def _process_word_chunk(self, chunk: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        results = []
        
        # Run one Word process for the entire chunk (30 files)
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0  # 0 = wdAlertsNone (disable all pop-up windows)

        try:
            for idx, wf in chunk:
                pdf_data = self._convert_single_document(word, wf)
                if pdf_data:
                    results.append((idx, pdf_data))
        finally:
            # Close the Word process after processing the chunk
            word.Quit()
            del word
            
        return results

    def _convert_single_document(self, word_app, file_path: Path) -> bytes | None:

        """Конвертація одного документа Word у відкритому додатку."""

        input_file = file_path.resolve()
        doc = None
        pdf_bytes = None
        
        # Create a unique temporary name for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)

        try:
            # Open document (ReadOnly=True — it is important for stability)
            doc = word_app.Documents.Open(str(input_file), ReadOnly=True, ConfirmConversions=False)
            doc.ExportAsFixedFormat(str(temp_pdf_path), 17)
            
            pdf_bytes = temp_pdf_path.read_bytes()
            
        except Exception as e:
            logger.error(f"❌  Word file error in {file_path.name}: {e}", exc_info = True)
        finally:
            if doc:
                doc.Close(SaveChanges=0) # 0 = wdDoNotSaveChanges
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
                
        return pdf_bytes
    