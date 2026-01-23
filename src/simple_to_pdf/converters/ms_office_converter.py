import gc
import logging
import tempfile
from pathlib import Path

import pythoncom  # pyright: ignore[reportMissingModuleSource]
import win32com.client as win32  # pyright: ignore[reportMissingModuleSource]

from src.simple_to_pdf.converters.img_converter import ImageConverter

logger = logging.getLogger(__name__)


class MSOfficeConverter(ImageConverter):
    SUPPORTED_FORMATS = {
        "table": {".xls", ".xlsx", ".xlsm", ".xlsb"},
        "document": {".doc", ".docx", ".docm", ".rtf", ".txt"},
        "presentation": {".ppt", ".pptx", ".pptm", ".pps", ".ppsx"},
    }

    def __init__(self, chunk_size: int = 30):
        super().__init__()
        self.chunk_size = chunk_size
        self.SUPPORTED_FORMATS = self.get_supported_formats()

    def convert_to_pdf(
        self, *, files: list[tuple[int, Path]]
    ) -> list[tuple[int, bytes]]:
        exls: list[tuple[int, Path]] = []
        wrds: list[tuple[int, Path]] = []
        imgs: list[tuple[int, Path]] = []
        ppts: list[tuple[int, Path]] = []
        final_results: list[tuple[int, bytes]] = []

        for idx, path in files:
            if not path.exists():
                continue
            if self.is_table_file(file_path=path):
                exls.append((idx, path))
            elif self.is_document_file(file_path=path):
                wrds.append((idx, path))
            elif self.is_presentation_file(file_path=path):
                ppts.append((idx, path))
            elif self.is_image_file(file_path=path):
                imgs.append((idx, path))

        if exls:
            final_results.extend(self._convert_tables_to_pdf(files=exls))
        if wrds:
            final_results.extend(self._convert_documents_to_pdf(word_files=wrds))
        if imgs:
            final_results.extend(self.convert_images_to_pdf(files=imgs))
        if ppts:
            final_results.extend(self._convert_presentations_to_pdf(files=ppts))

        return final_results

    def _convert_presentations_to_pdf(
        self, *, ppt_files: list[tuple[int, Path]]
    ) -> list[tuple[int, bytes]]:
        all_results = []
        # Splitting into chunks to avoid overloading memory
        for chunk in self.make_chunks(ppt_files, n=self.chunk_size):
            all_results.extend(self._process_presentation_chunk(chunk))
        return all_results

    def _process_presentation_chunk(
        self, *, chunk: list[tuple[int, Path]]
    ) -> list[tuple[int, bytes]]:
        results = []
        # Important for workers in background threads
        pythoncom.CoInitialize()
        app_name = "PowerPoint.Application"
        try:
            # Using EnsureDispatch for stability in .exe (Nuitka)
            powerpoint = win32.gencache.EnsureDispatch("PowerPoint.Application")

            for idx, pf in chunk:
                pdf_data = self._convert_single_presentation(
                    ppt_app=powerpoint, file_path=pf
                )
                if pdf_data:
                    results.append((idx, pdf_data))

        except Exception as e:
            logger.error(f"❌ PowerPoint chunk error: {e}", exc_info=True)
        finally:
            self._safe_release_com_object(obj=powerpoint, app_name=app_name)
            pythoncom.CoUninitialize()

        return results

    def _convert_single_presentation(self, *, ppt_app, file_path: Path) -> bytes | None:
        """Conversion of a single PowerPoint presentation."""

        input_file = file_path.resolve()
        pres = None
        pdf_bytes = None

        # Creating a unique temporary file for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)

        try:
            # WithWindow=0 — critical! Opens PPT without showing a window on the screen.
            pres = ppt_app.Presentations.Open(
                str(input_file), ReadOnly=True, WithWindow=0
            )
            pres.SaveAs(str(temp_pdf_path), win32.constants.ppSaveAsPDF)
            pdf_bytes = temp_pdf_path.read_bytes()

        except Exception as e:
            logger.error(
                f"❌ PowerPoint file error in {file_path.name}: {e}", exc_info=True
            )
        finally:
            if pres:
                try:
                    pres.Close()
                except:  # noqa: E722
                    pass
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()

        return pdf_bytes

    def _convert_tables_to_pdf(
        self, *, files: list[tuple[int, Path]]
    ) -> list[tuple[int, bytes]]:
        all_results = []
        # Split for chunks
        for chunk in self.make_chunks(files, n=self.chunk_size):
            all_results.extend(self._process_table_chunk(chunk))

        return all_results

    def _process_table_chunk(
        self, chunk: list[tuple[int, Path]]
    ) -> list[tuple[int, bytes]]:
        results = []
        # Run Excel only for this chunk
        pythoncom.CoInitialize()
        app_name: str = "Excel.Application"

        try:
            excel = win32.gencache.EnsureDispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False  # Disable alerts to prevent pop-ups
            for idx, f in chunk:
                pdf_data = self._convert_single_table(excel, f)
                if pdf_data:
                    results.append((idx, pdf_data))
        finally:
            self._safe_release_com_object(obj=excel, app_name=app_name)
        pythoncom.CoUninitialize()
        return results

    def _prepare_table_for_export(self, wb):
        """Setup printing options"""

        for sheet in wb.Sheets:
            width = sheet.UsedRange.Columns.Count

            # Налаштовуємо орієнтацію
            sheet.PageSetup.Orientation = 2 if width > 10 else 1

            # Налаштовуємо масштабування
            sheet.PageSetup.Zoom = False
            sheet.PageSetup.FitToPagesWide = 1
            sheet.PageSetup.FitToPagesTall = False
            sheet.PageSetup.FitToPagesTall = False

    def _convert_single_table(self, excel_app, file_path: Path) -> bytes | None:
        """Converting a single file inside the opened application."""

        input_file = file_path.resolve()
        wb = None
        pdf_bytes = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)

        try:
            wb = excel_app.Workbooks.Open(str(input_file), ReadOnly=True)
            self._prepare_table_for_export(wb=wb)
            wb.ExportAsFixedFormat(0, str(temp_pdf_path))
            pdf_bytes = temp_pdf_path.read_bytes()
        except Exception as e:
            logger.error(
                f"❌  Table file error in {file_path.name}: {e}", exc_info=True
            )
        finally:
            if wb:
                wb.Close(SaveChanges=False)
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()

        return pdf_bytes

    def _convert_documents_to_pdf(
        self, *, word_files: list[tuple[int, Path]]
    ) -> list[tuple[int, bytes]]:
        all_results = []

        # Convert by chunks of 30 files
        for chunk in self.make_chunks(word_files, n=self.chunk_size):
            all_results.extend(self._process_documents_chunk(chunk))

        return all_results

    def _process_documents_chunk(
        self, chunk: list[tuple[int, Path]]
    ) -> list[tuple[int, bytes]]:
        results = []
        pythoncom.CoInitialize()
        app_name: str = "Word.Application"
        try:
            word = win32.gencache.EnsureDispatch(app_name)
            # Run one Word process for the entire chunk (30 files)
            word.Visible = False
            word.DisplayAlerts = 0  # 0 = wdAlertsNone (disable all pop-up windows)
            for idx, wf in chunk:
                pdf_data = self._convert_single_document(word, wf)
                if pdf_data:
                    results.append((idx, pdf_data))
        finally:
            self._safe_release_com_object(obj=word, app_name=app_name)
        pythoncom.CoUninitialize()
        return results

    def _convert_single_document(self, word_app, file_path: Path) -> bytes | None:
        """Conversion of a single Word document within the open application."""

        input_file = file_path.resolve()
        doc = None
        pdf_bytes = None

        # Create a unique temporary name for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)

        try:
            # Open document (ReadOnly=True — it is important for stability)
            doc = word_app.Documents.Open(
                str(input_file), ReadOnly=True, ConfirmConversions=False
            )
            doc.ExportAsFixedFormat(str(temp_pdf_path), 17)

            pdf_bytes = temp_pdf_path.read_bytes()

        except Exception as e:
            logger.error(
                f"❌  Document file error in {file_path.name}: {e}", exc_info=True
            )
        finally:
            if doc:
                doc.Close(SaveChanges=0)  # 0 = wdDoNotSaveChanges
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()

        return pdf_bytes

    def _safe_release_com_object(self, *, obj, app_name: str = "Office App"):
        """Safely closes the Office application and releases COM resources."""

        if obj:
            try:
                # Check for specific close methods
                if hasattr(obj, "Quit"):
                    obj.Quit()
                elif hasattr(obj, "Close"):
                    obj.Close()
                logger.info(f"✅ {app_name} closed successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Could not close {app_name} gracefully: {e}")
            finally:
                # Explicitly delete the reference and trigger garbage collection
                # This is crucial for preventing 'zombie' processes in Task Manager
                del obj
                gc.collect()
