import gc
import logging
import shutil
import sys
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Any

import pythoncom  # pyright: ignore[reportMissingModuleSource]
import win32com.client as win32  # pyright: ignore[reportMissingModuleSource]
from win32com.client import gencache

from simple_to_pdf.converters.img_converter import ImageConverter
from simple_to_pdf.converters.models import ConversionResult
from simple_to_pdf.converters.ms_mixin import MSSetupMixin

logger = logging.getLogger(__name__)


class OfficeApp(StrEnum):
    WORD = "Word.Application"
    EXCEL = "Excel.Application"
    POWERPOINT = "PowerPoint.Application"


class MSOfficeConverter(ImageConverter, MSSetupMixin):
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
            tables_res: ConversionResult = self._convert_files_to_pdf(
                files=tables, app_type=OfficeApp.EXCEL
            )
            final_results.success.extend(tables_res.success)
            final_results.failed.extend(tables_res.failed)
        if docs:
            docs_res: ConversionResult = self._convert_files_to_pdf(
                files=docs, app_type=OfficeApp.WORD
            )
            final_results.success.extend(docs_res.success)
            final_results.failed.extend(docs_res.failed)
        if pres:
            pres_res: ConversionResult = self._convert_files_to_pdf(
                files=pres, app_type=OfficeApp.POWERPOINT
            )
            final_results.success.extend(pres_res.success)
            final_results.failed.extend(pres_res.failed)
        if imgs:
            imgs_res: ConversionResult = self._convert_images_to_pdf(files=imgs)
            final_results.success.extend(imgs_res.success)
            final_results.failed.extend(imgs_res.failed)

        return final_results

    def _convert_files_to_pdf(
        self, *, files: list[tuple[int, Path]], app_type: str
    ) -> ConversionResult:
        all_results: ConversionResult = ConversionResult()
        chunk_results: ConversionResult = ConversionResult()
        if not files:
            return all_results

        # Splitting into chunks to avoid overloading memory
        for chunk in self.make_chunks(files, n=self.chunk_size):
            match app_type:
                case OfficeApp.POWERPOINT:
                    chunk_results: ConversionResult = self._process_presentation_chunk(
                        chunk=chunk
                    )
                case OfficeApp.EXCEL:
                    chunk_results: ConversionResult = self._process_table_chunk(
                        chunk=chunk
                    )
                case OfficeApp.WORD:
                    chunk_results: ConversionResult = self._process_documents_chunk(
                        chunk=chunk
                    )
                case _:
                    logger.error(f"Unknown app_type: {app_type}")
                    continue
            all_results.success.extend(chunk_results.success)
            all_results.failed.extend(chunk_results.failed)

        return all_results

    def _get_app_instance(self, *, app_type: str):
        """
        Creates isolated COM application instance using late binding.

        If COM launch fails due to possible corrupted win32com cache,
        attempts emergency cache cleanup and retries once.
        """

        try:
            return win32.DispatchEx(app_type)

        except Exception as e:
            logger.warning(
                f"DispatchEx failed for {app_type}: {e}",
                exc_info=True,
            )

            try:
                logger.info("Attempting win32com cache cleanup")
                self._clear_cache()
                return win32.DispatchEx(app_type)

            except Exception as e_crit:
                logger.error(
                    f"Critical Error: Failed to create COM instance "
                    f"for {app_type}: {e_crit}",
                    exc_info=True,
                )

                return None

    def _clear_cache(self) -> None:
        """
        Clears win32com gen_py cache from memory and disk.
        Used only as emergency recovery fallback.
        """

        try:
            # Remove loaded gen_py modules from memory
            for module_name in list(sys.modules):
                if module_name.startswith("win32com.gen_py"):
                    sys.modules.pop(module_name, None)

            # Remove cache folder from disk
            cache_dir = Path(gencache.GetGeneratePath())

            if cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=True)

            logger.info("win32com cache cleared")

        except Exception as e:
            logger.warning(
                f"Failed to clear cache: {e}",
                exc_info=True,
            )

    def _process_presentation_chunk(
        self, *, chunk: list[tuple[int, Path]]
    ) -> ConversionResult:
        chunk_res: ConversionResult = ConversionResult()

        # Important for workers in background threads
        pythoncom.CoInitialize()
        powerpoint = None
        app_type: str = OfficeApp.POWERPOINT
        try:
            # Using EnsureDispatch for stability in .exe (Nuitka)
            powerpoint = self._get_app_instance(app_type=app_type)

            if powerpoint is None:
                raise RuntimeError(f"Could not initialize {app_type}.")

            for idx, pf in chunk:
                pdf_data = None
                try:
                    pdf_data = self._convert_single_presentation(
                        ppt_app=powerpoint, file_path=pf
                    )
                    chunk_res.success.append((idx, pdf_data))
                except Exception:
                    chunk_res.failed.append((idx, pf))

        except Exception as e:
            logger.error(f"Presentations chunk error: {e}", exc_info=True)
            already_done = {item[0] for item in chunk_res.success} | {
                item[0] for item in chunk_res.failed
            }
            for idx, pf in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx, pf))
        finally:
            self._safe_release_com_object(obj=powerpoint, app_type=app_type)
            powerpoint = None
            gc.collect()
            pythoncom.CoUninitialize()

        return chunk_res

    def _process_table_chunk(self, chunk: list[tuple[int, Path]]) -> ConversionResult:
        chunk_res: ConversionResult = ConversionResult()

        # Run Excel only for this chunk
        pythoncom.CoInitialize()
        excel = None
        app_type: str = OfficeApp.EXCEL

        try:
            excel = self._get_app_instance(app_type=app_type)
            if excel is None:
                raise RuntimeError(f"Could not initialize {app_type}.")

            excel.Visible = False
            excel.DisplayAlerts = False  # Disable alerts to prevent pop-ups
            for idx, f in chunk:
                pdf_data = None
                try:
                    pdf_data = self._convert_single_table(excel, f)
                    chunk_res.success.append((idx, pdf_data))
                except Exception:
                    chunk_res.failed.append((idx, f))
        except Exception as e:
            logger.error(f"Tables chunk error: {e}", exc_info=True)
            already_done = {item[0] for item in chunk_res.success} | {
                item[0] for item in chunk_res.failed
            }
            for idx, f in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx, f))
        finally:
            self._safe_release_com_object(obj=excel, app_type=app_type)
            excel = None
            gc.collect()
            pythoncom.CoUninitialize()
        return chunk_res

    def _process_documents_chunk(
        self, chunk: list[tuple[int, Path]]
    ) -> ConversionResult:
        chunk_res: ConversionResult = ConversionResult()
        pythoncom.CoInitialize()
        word = None
        app_type: str = OfficeApp.WORD
        try:
            word = self._get_app_instance(app_type=app_type)
            if word is None:
                raise RuntimeError(f"Could not initialize {app_type}.")
            # Run one Word process for the entire chunk (30 files)
            word.Visible = False
            word.DisplayAlerts = 0  # 0 = wdAlertsNone (disable all pop-up windows)
            for idx, wf in chunk:
                try:
                    pdf_data = self._convert_single_document(word, wf)
                    chunk_res.success.append((idx, pdf_data))
                except Exception:
                    chunk_res.failed.append((idx, wf))
        except Exception as e:
            logger.error(f"Documents chunk error: {e}", exc_info=True)
            already_done = {item[0] for item in chunk_res.success} | {
                item[0] for item in chunk_res.failed
            }
            for idx, wf in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx, wf))
        finally:
            self._safe_release_com_object(obj=word, app_type=app_type)
            word = None
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
            pres.SaveAs(str(temp_pdf_path), 32)
            pdf_bytes = temp_pdf_path.read_bytes()

        except Exception as e:
            logger.error(
                f"PowerPoint file error in {file_path.name}: {e}", exc_info=True
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

    def _convert_single_table(self, excel_app, file_path: Path) -> bytes:
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

    def _convert_single_document(self, word_app, file_path: Path) -> bytes:
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

    def _safe_release_com_object(self, *, obj, app_type: str = "Office App"):
        """Safely closes the Office application and releases COM resources."""

        if obj:
            try:
                # Check for specific close methods
                if hasattr(obj, "Quit"):
                    obj.Quit()
                logger.info(f"✅ {app_type} closed successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Could not close {app_type} gracefully: {e}")
