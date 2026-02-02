import gc
import logging
import tempfile
from pathlib import Path

import pythoncom  # pyright: ignore[reportMissingModuleSource]
import win32com.client as win32  # pyright: ignore[reportMissingModuleSource]
from src.simple_to_pdf.converters.img_converter import ImageConverter
from src.simple_to_pdf.converters.models import ConversionResult

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
    ) -> ConversionResult:
        tables: list[tuple[int, Path]] = []
        docs: list[tuple[int, Path]] = []
        imgs: list[tuple[int, Path]] = []
        pres: list[tuple[int, Path]] = []
        final_results: ConversionResult = ConversionResult()

        for idx, path in files:
            if not path.exists():
                continue
            if self.is_table_file(file_path=path):
                tables.append((idx, path))
            elif self.is_document_file(file_path=path):
                docs.append((idx, path))
            elif self.is_presentation_file(file_path=path):
                pres.append((idx, path))
            elif self.is_image_file(file_path=path):
                imgs.append((idx, path))

        if tables:
            tables_res:ConversionResult=self._convert_tables_to_pdf(files=tables)
            final_results.successful.extend(tables_res.successful)
            final_results.failed.extend(tables_res.failed)
        if docs:
            docs_res:ConversionResult=self._convert_documents_to_pdf(word_files=docs)
            final_results.successful.extend(docs_res.successful)
            final_results.failed.extend(docs_res.failed)
        if imgs:
            imgs_res:ConversionResult=self.convert_images_to_pdf(files=imgs)
            final_results.successful.extend(imgs_res.successful)
            final_results.failed.extend(imgs_res.failed)
        if pres:
            pres_res:ConversionResult=self._convert_presentations_to_pdf(files=pres)
            final_results.successful.extend( pres_res.successful)
            final_results.failed.extend( pres_res.failed)

        return final_results

    def _convert_presentations_to_pdf(
        self, *, files: list[tuple[int, Path]]
    ) -> ConversionResult:
        all_results:ConversionResult = ConversionResult()
        # Splitting into chunks to avoid overloading memory
        for chunk in self.make_chunks(files, n=self.chunk_size):
            chunk_results:ConversionResult=self._process_presentation_chunk(chunk = chunk)
            all_results.successful.extend(chunk_results.successful)
            all_results.failed.extend(chunk_results.failed)
            
        return all_results
    
    def _get_app_instance(self,*,app_name: str):
        """
        Creates a robust COM application instance using a fallback mechanism.
        If the early-bound (gencache) version fails due to corrupted cache, 
        it falls back to a dynamic late-bound instance.
        """
        app = None
        try:
            # Primary Attempt: Standard DispatchEx (isolated process)
            # May fail here if the win32com cache (gen_py) is corrupted
            app = win32.DispatchEx(app_name)
        
            try:
                # Try to upgrade to an early-bound instance for better performance/constants
                return win32.gencache.EnsureDispatch(app)
            except Exception as e:
                logger.warning(f"⚠️ Gencache failed for {app_name}, using raw DispatchEx: {e}",exc_info=True)
                return app
            
        except Exception as e:
            logger.warning(f"⚠️ Standard DispatchEx failed for {app_name}, trying dynamic fallback: {e}",exc_info=True)
            try:
                # Final Fallback: Dynamic Dispatch (completely ignores gen_py cache)
                return win32.dynamic.DispatchEx(app_name)
            except Exception as e_crit:
                logger.error(f"❌ Critical Error: All launch methods failed for {app_name}: {e_crit}",exc_info=True)
                return None

    def _process_presentation_chunk(
        self, *, chunk: list[tuple[int, Path]]
    ) -> ConversionResult:
        
        chunk_res:ConversionResult=ConversionResult()

        # Important for workers in background threads
        pythoncom.CoInitialize()
        app_name = "PowerPoint.Application"
        try:
            # Using EnsureDispatch for stability in .exe (Nuitka)
            powerpoint = self._get_app_instance(app_name=app_name)

            if powerpoint is None:
                raise RuntimeError(f"❌ Could not initialize {app_name}.")

            for idx, pf in chunk:
                pdf_data = None
                try:
                    pdf_data = self._convert_single_presentation(
                        ppt_app=powerpoint, file_path=pf
                    )
                    chunk_res.successful.append((idx, pdf_data))
                except Exception:
                    chunk_res.failed.append((idx,pf))

        except Exception as e:
            logger.error(f"❌ Presentations chunk error: {e}", exc_info=True)
            already_done = chunk_res.processed_ids
            for idx, pf in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx,pf))
        finally:
            self._safe_release_com_object(obj=powerpoint, app_name=app_name)
            powerpoint=None
            gc.collect()
            pythoncom.CoUninitialize()

        return chunk_res

    def _convert_single_presentation(self, *, ppt_app, file_path: Path) -> bytes:

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
            raise
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
    ) -> ConversionResult:
        all_results:ConversionResult = ConversionResult()
        # Split for chunks
        for chunk in self.make_chunks(files, n=self.chunk_size):
            chunk_res:ConversionResult=self._process_table_chunk(chunk=chunk)
            all_results.successful.extend(chunk_res.successful)
            all_results.failed.extend(chunk_res.failed)
        return all_results

    def _process_table_chunk(
        self, chunk: list[tuple[int, Path]]
    ) -> ConversionResult:
        chunk_res:ConversionResult=ConversionResult()

        # Run Excel only for this chunk
        pythoncom.CoInitialize()
        app_name: str = "Excel.Application"

        try:
            excel = self._get_app_instance(app_name=app_name)
            if excel is None:
                raise RuntimeError(f"❌ Could not initialize {app_name}.")
            
            excel.Visible = False
            excel.DisplayAlerts = False  # Disable alerts to prevent pop-ups
            for idx, f in chunk:
                pdf_data=None
                try:
                    pdf_data = self._convert_single_table(excel, f)
                    chunk_res.successful.append((idx,pdf_data))
                except Exception:
                     chunk_res.failed.append((idx,f))
        except Exception as e:
            logger.error(f"❌ Tables chunk error: {e}", exc_info=True)
            already_done = chunk_res.processed_ids
            for idx, f in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx,f))
        finally:
            self._safe_release_com_object(obj=excel, app_name=app_name)
            excel=None
            gc.collect()
            pythoncom.CoUninitialize()
        return chunk_res

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
            raise
        finally:
            if wb:
                wb.Close(SaveChanges=False)
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()

        return pdf_bytes

    def _convert_documents_to_pdf(
        self, *, word_files: list[tuple[int, Path]]
    ) -> ConversionResult:
        all_results:ConversionResult =ConversionResult()
        
        # Convert by chunks of 30 files
        for chunk in self.make_chunks(word_files, n=self.chunk_size):
            chunk_res:ConversionResult=self._process_documents_chunk(chunk=chunk)
            all_results.successful.extend(chunk_res.successful)
            all_results.failed.extend(chunk_res.failed)
        return all_results

    def _process_documents_chunk(
        self, chunk: list[tuple[int, Path]]
    ) ->ConversionResult:
        chunk_res:ConversionResult=ConversionResult()
        pythoncom.CoInitialize()
        app_name: str = "Word.Application"
        try:
            word = self._get_app_instance(app_name=app_name)
            if word is None:
                raise RuntimeError(f"❌ Could not initialize {app_name}.")
            # Run one Word process for the entire chunk (30 files)
            word.Visible = False
            word.DisplayAlerts = 0  # 0 = wdAlertsNone (disable all pop-up windows)
            for idx, wf in chunk:
                pdf_data=None
                try:
                    pdf_data = self._convert_single_document(word, wf)
                    chunk_res.successful.append((idx,pdf_data))
                except Exception:
                    chunk_res.failed.append((idx,wf))
        except Exception as e:
            logger.error(f"❌ Documents chunk error: {e}", exc_info=True)
            already_done = chunk_res.processed_ids
            for idx, wf in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx,wf))
        finally:
            self._safe_release_com_object(obj=word, app_name=app_name)
            word=None
            gc.collect()
            pythoncom.CoUninitialize()
        return chunk_res

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
                f"❌  Document file error in {input_file.name}: {e}", exc_info=True
            )
            raise
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
                logger.info(f"✅ {app_name} closed successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Could not close {app_name} gracefully: {e}")
