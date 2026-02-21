import gc
import logging
import tempfile
from pathlib import Path
from typing import Any
import pythoncom  # pyright: ignore[reportMissingModuleSource]
import win32com.client as win32  # pyright: ignore[reportMissingModuleSource]

from simple_to_pdf.converters.img_converter import ImageConverter
from simple_to_pdf.converters.models import ConversionResult
from simple_to_pdf.converters.ms_excel_formater import MSExcelFormattingMixin
from enum import Enum
logger = logging.getLogger(__name__)

class AppServiceName(Enum):
   
    EXCEL = "Excel.Application"
    WORD = "Word.Application"
    POWERPOINT ="PowerPoint.Application"

    @property
    def prog_id(self):
        return self.value[0]

    @property
    def display_name(self):
        return self.value[1]
    
class MSOfficeConverter(ImageConverter,MSExcelFormattingMixin):
    SUPPORTED_FORMATS = {
        "table": {".xls", ".xlsx", ".xlsm", ".xlsb"},
        "document": {".doc", ".docx", ".docm", ".rtf", ".txt"},
        "presentation": {".ppt", ".pptx", ".pptm", ".pps", ".ppsx"},
    }

    def __init__(self, chunk_size: int = 30):
        super().__init__(chunk_size=chunk_size)
        self.SUPPORTED_FORMATS = self.get_supported_formats()

    def convert_to_pdf(self, *, files: list[tuple[int, Path]]) -> ConversionResult:
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
            tables_res: ConversionResult = self._convert_file_to_pdf(files=tables,app_name=AppServiceName.EXCEL.prog_id)
            final_results.successful.extend(tables_res.successful)
            final_results.failed.extend(tables_res.failed)
        if docs:
            docs_res: ConversionResult = self._convert_file_to_pdf(files=docs,app_name=AppServiceName.WORD.prog_id)
            final_results.successful.extend(docs_res.successful)
            final_results.failed.extend(docs_res.failed)
        if pres:
            pres_res: ConversionResult = self._convert_file_to_pdf(files=pres,app_name=AppServiceName.POWERPOINT.prog_id)
            final_results.successful.extend(pres_res.successful)
            final_results.failed.extend(pres_res.failed)
        if imgs:
            imgs_res: ConversionResult = self._convert_images_to_pdf(files=imgs)
            final_results.successful.extend(imgs_res.successful)
            final_results.failed.extend(imgs_res.failed)
        

        return final_results

    def _convert_file_to_pdf(
        self, *, files: list[tuple[int, Path]],app_name:str
    ) -> ConversionResult:
        all_results: ConversionResult = ConversionResult()
        # Splitting into chunks to avoid overloading memory
        for chunk in self.make_chunks(files, n=self.chunk_size):
            chunk_results: ConversionResult = self._process_chunk(
                chunk=chunk,
                app_name=app_name
            )
            all_results.successful.extend(chunk_results.successful)
            all_results.failed.extend(chunk_results.failed)

        return all_results


    def _get_app_instance(self, *, app_name: str):
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
                return win32.gencache.EnsureDispatch(app)# type: ignore
            except Exception as e:
                logger.warning(
                    f"⚠️ Gencache failed for {app_name}, using raw DispatchEx: {e}",
                    exc_info=True,
                )
                return app

        except Exception as e:
            logger.warning(
                f"⚠️ Standard DispatchEx failed for {app_name}, trying dynamic fallback: {e}",
                exc_info=True,
            )
            try:
                # Final Fallback: Dynamic Dispatch (completely ignores gen_py cache)
                return win32.dynamic.DispatchEx(app_name) # type: ignore
            except Exception as e_crit:
                logger.error(
                    f"❌ Critical Error: All launch methods failed for {app_name}: {e_crit}",
                    exc_info=True,
                )
                return None

    def _process_chunk(
        self, *, chunk: list[tuple[int, Path]], app_name: str
    ) -> ConversionResult:
        chunk_res: ConversionResult = ConversionResult()

        # Important for workers in background threads
        pythoncom.CoInitialize()
        app = None
        try:
            # Using EnsureDispatch for stability in .exe (Nuitka)
            app = self._get_app_instance(app_name=app_name)

            if app is None:
                raise RuntimeError(f"❌ Could not initialize {app_name}.")

            for idx, pf in chunk:
                pdf_data = None
                try:
                    pdf_data = self._convert_single_file(
                        app=app, file_path=pf
                    )
                    chunk_res.successful.append((idx, pdf_data))
                except Exception:
                    chunk_res.failed.append((idx, pf))

        except Exception as e:
            logger.error(f"❌ Presentations chunk error: {e}", exc_info=True)
            already_done = chunk_res.processed_ids
            for idx, pf in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx, pf))
        finally:
            self._safe_release_com_object(obj=app, app_name=app_name)
            app= None
            gc.collect()
            pythoncom.CoUninitialize()

        return chunk_res

    def _open_office_document(self, app: Any, file_path: Path) -> Any:
        """
        Dynamically opens an Office document based on the application type.
        """
        input_file = str(file_path.resolve())
        app_name = app.Name # Gets "Microsoft Excel", etc.
        
        # Mapping Display Names to their respective collection names
        collections = {
            AppServiceName.EXCEL.display_name: "Workbooks",
            AppServiceName.WORD.display_name: "Documents",
            AppServiceName.POWERPOINT.display_name: "Presentations"
        }
        
        # Determine collection name
        collection_name = collections.get(app_name, "Workbooks")
        
        try:
            collection = getattr(app, collection_name)
            
            # PowerPoint specific open logic
            if AppServiceName.POWERPOINT.display_name in app_name:
                return collection.Open(input_file, ReadOnly=True, WithWindow=False)
            
            # Excel and Word standard open
            return collection.Open(input_file, ReadOnly=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to open {file_path.name} via {app_name}: {e}")
            raise

    def _get_export_format(self, app_name: str) -> int:
        """Returns the specific PDF export format code for each Office application."""
        if AppServiceName.EXCEL.display_name in app_name:
            return 0  # xlTypePDF
        if AppServiceName.WORD.display_name in app_name:
            return 17 # wdExportFormatPDF
        if AppServiceName.POWERPOINT.display_name in app_name:
            return 32 # ppFixedFormatTypePDF
        return 0

    def _convert_single_file(self, app: Any, file_path: Path) -> bytes:
        """
        Processes a single file: Open -> Prepare (Excel only) -> Export -> Cleanup.
        """
        opened_file = None
        pdf_bytes = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf_path = Path(tmp.name)

        try:
            opened_file = self._open_office_document(app=app, file_path=file_path)
            
            app_name = app.Name
            # Apply Excel-specific formatting if needed
            if AppServiceName.EXCEL.display_name in app_name:
                self._prepare_table_for_export(workbook=opened_file)
            
            export_fmt = self._get_export_format(app_name)

            # Export logic
            if AppServiceName.POWERPOINT.display_name in app_name:
                # PowerPoint signature: Path is the 1st arg, Type is the 2nd
                opened_file.ExportAsFixedFormat(str(temp_pdf_path), export_fmt)
            else:
                # Word/Excel signature: Type is the 1st arg, Path is the 2nd
                opened_file.ExportAsFixedFormat(export_fmt, str(temp_pdf_path))
            
            pdf_bytes = temp_pdf_path.read_bytes()

        except Exception as e:
            logger.error(f"❌ Conversion error for {file_path.name}: {e}", exc_info=True)
            raise
        finally:
            if opened_file:
                try:
                    opened_file.Close(SaveChanges=False)
                except Exception as close_err:
                    logger.debug(f"Could not close file: {close_err}")
            
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
