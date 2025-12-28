from pathlib import Path
from .base_converter import BaseConverter
import tempfile
import win32com.client as win32

class MSOfficeConverter(BaseConverter):
    def __init__(self, chunk_size: int = 30):  # Додай цей параметр
        super().__init__()
        self.chunk_size = chunk_size

    def convert_to_pdf(self, *, files: list[tuple[int, str]]) -> list[tuple[int, bytes]]:
        # 1-й рівень (всередині методу)
        exls: list[tuple[int, Path]] = []
        wrds: list[tuple[int, Path]] = []
        imgs: list[tuple[int, Path]] = []
        final_results: list[tuple[int, bytes]] = []

        for idx, path_str in files:
            # 2-й рівень (всередині циклу)
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

        # Повертаємось на 1-й рівень
        if exls:
            final_results.extend(self._convert_excel_to_pdf(files=exls))
        if wrds:
            final_results.extend(self._convert_word_to_pdf(word_files=wrds))
        if imgs:
            final_results.extend(self.convert_images_to_pdf(files=imgs))

        final_results.sort(key=lambda x: x[0])
        return final_results
    
    def _convert_excel_to_pdf(self, *, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        all_results = []
        
        # Ділимо на чанки, щоб Excel не "втомився"
        for chunk in self.make_chunks(files, n=self.chunk_size):
            all_results.extend(self._process_excel_chunk(chunk))
        
        return all_results

    def _process_excel_chunk(self, chunk: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        results = []
        # Запускаємо Excel тільки для цього чанку
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False # Щоб не вискакували вікна підтвердження

        try:
            for idx, f in chunk:
                pdf_data = self._convert_single_excel(excel, f)
                if pdf_data:
                    results.append((idx, pdf_data))
        finally:
            excel.Quit() # Закриваємо Excel після 30 файлів
            del excel
            
        return results

    def _convert_single_excel(self, excel_app, file_path: Path) -> bytes | None:
        """Логіка конвертації ОДНОГО файлу всередині відкритого додатка."""
        input_file = file_path.resolve()
        wb = None
        pdf_bytes = None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)

        try:
            wb = excel_app.Workbooks.Open(str(input_file), ReadOnly=True)
            # 0 — це формат PDF
            wb.ExportAsFixedFormat(0, str(temp_pdf_path))
            pdf_bytes = temp_pdf_path.read_bytes()
        except Exception as e:
            print(f"❌ Помилка Excel на файлі {file_path.name}: {e}")
        finally:
            if wb:
                wb.Close(SaveChanges=False)
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
                
        return pdf_bytes
               
    def _convert_word_to_pdf(self, *, word_files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        all_results = []
        
        # Обробляємо чанками по 30 файлів
        for chunk in self.make_chunks(word_files, n=self.chunk_size):
            all_results.extend(self._process_word_chunk(chunk))
            
        return all_results

    def _process_word_chunk(self, chunk: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        results = []
        
        # Запускаємо один процес Word на весь чанк (30 файлів)
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0  # 0 = wdAlertsNone (вимикаємо всі спливаючі вікна)

        try:
            for idx, wf in chunk:
                pdf_data = self._convert_single_document(word, wf)
                if pdf_data:
                    results.append((idx, pdf_data))
        finally:
            # Закриваємо процес Word після обробки чанку
            word.Quit()
            del word
            
        return results

    def _convert_single_document(self, word_app, file_path: Path) -> bytes | None:
        """Конвертація одного документа Word у відкритому додатку."""
        input_file = file_path.resolve()
        doc = None
        pdf_bytes = None
        
        # Створюємо унікальне тимчасове ім'я для PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)

        try:
            # Відкриваємо документ (ReadOnly=True — це важливо для стабільності)
            doc = word_app.Documents.Open(str(input_file), ReadOnly=True, ConfirmConversions=False)
            
            # 17 — це константа wdExportFormatPDF
            # Ми використовуємо ExportAsFixedFormat, бо це найнадійніший метод
            doc.ExportAsFixedFormat(str(temp_pdf_path), 17)
            
            pdf_bytes = temp_pdf_path.read_bytes()
            
        except Exception as e:
            print(f"❌ Помилка Word на файлі {file_path.name}: {e}")
        finally:
            if doc:
                doc.Close(SaveChanges=0) # 0 = wdDoNotSaveChanges
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
                
        return pdf_bytes


                
               
    

