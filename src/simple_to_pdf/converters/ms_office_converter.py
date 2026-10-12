import gc
import logging
import shutil
import sys
from enum import StrEnum
from pathlib import Path

import pythoncom  # pyright: ignore[reportMissingModuleSource]
import win32com.client as win32  # pyright: ignore[reportMissingModuleSource]
from win32com.client import gencache  # pyright: ignore[reportMissingModuleSource]

from simple_to_pdf.converters.img_converter import ImageConverter
from simple_to_pdf.converters.models import ConversionResult
from simple_to_pdf.converters.ms_mixin import MSSetupMixin
from simple_to_pdf.utils.file_tools import get_unique_path

logger = logging.getLogger(__name__)


class OfficeApp(StrEnum):
    WORD = "Word.Application"
    EXCEL = "Excel.Application"
    POWERPOINT = "PowerPoint.Application"


class MSOfficeConverter(ImageConverter, MSSetupMixin):
    SUPPORTED_FORMATS = {  # noqa: RUF012
        "table": {".xls", ".xlsx", ".xlsm", ".xlsb"},
        "document": {".doc", ".docx", ".docm", ".rtf", ".txt"},
        "presentation": {".ppt", ".pptx", ".pptm", ".pps", ".ppsx"},
    }
    OFFICE_CONFIG = {  # noqa: RUF012
        OfficeApp.EXCEL: {
            "visible": False,
            "display_alerts": False,
        },
        OfficeApp.WORD: {
            "visible": False,
            "display_alerts": 0,  # 0 = wdAlertsNone
        },
        OfficeApp.POWERPOINT: {
            "display_alerts": False,
        },
    }

    def __init__(self, chunk_size: int = 30):
        super().__init__(chunk_size=chunk_size)
        self.SUPPORTED_FORMATS = self.get_supported_formats()

    def convert_to_pdf(
        self, *, files: list[tuple[int, Path]], out_dir: Path
    ) -> ConversionResult:
        """Categorize files by type, route to specific conversion services, and aggregate the results."""
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
                files=tables, app_type=OfficeApp.EXCEL, out_dir=out_dir
            )
            final_results.success.extend(tables_res.success)
            final_results.failed.extend(tables_res.failed)
        if docs:
            docs_res: ConversionResult = self._convert_files_to_pdf(
                files=docs, app_type=OfficeApp.WORD, out_dir=out_dir
            )
            final_results.success.extend(docs_res.success)
            final_results.failed.extend(docs_res.failed)
        if pres:
            pres_res: ConversionResult = self._convert_files_to_pdf(
                files=pres, app_type=OfficeApp.POWERPOINT, out_dir=out_dir
            )
            final_results.success.extend(pres_res.success)
            final_results.failed.extend(pres_res.failed)
        if imgs:
            imgs_res: ConversionResult = self._convert_images_to_pdf(
                files=imgs, out_dir=out_dir
            )
            final_results.success.extend(imgs_res.success)
            final_results.failed.extend(imgs_res.failed)

        return final_results

    def _convert_files_to_pdf(
        self, *, files: list[tuple[int, Path]], app_type: OfficeApp, out_dir: Path
    ) -> ConversionResult:
        """Convert a list of files to PDF by routing to the appropriate processor based on the application type."""
        all_results: ConversionResult = ConversionResult()
        chunk_results: ConversionResult = ConversionResult()
        if not files:
            return all_results

        for chunk in self.make_chunks(files, n=self.chunk_size):
            chunk_results: ConversionResult = self._process_chunk(
                chunk=chunk, app_type=app_type, out_dir=out_dir
            )
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

            except Exception:
                logger.exception(
                    "Critical Error: Failed to create COM instance for %s", app_type
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

            cache_dir = Path(gencache.GetGeneratePath())

            if cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=True)

            logger.info("win32com cache cleared")

        except Exception as e:
            logger.warning(
                f"Failed to clear cache: {e}",
                exc_info=True,
            )

    def _get_processor(self, *, app_type: OfficeApp):
        processors = {
            OfficeApp.WORD: self._convert_doc_to_pdf,
            OfficeApp.EXCEL: self._convert_table_to_pdf,
            OfficeApp.POWERPOINT: self._convert_pres_to_pdf,
        }
        return processors[app_type]

    def _disable_visibility(self, *, app, app_type: OfficeApp) -> None:
        config = self.OFFICE_CONFIG.get(app_type)
        if not config:
            logger.warning(f"No configuration found for {app_type}.")
            return

        if "visible" in config and hasattr(app, "Visible"):
            try:
                app.Visible = config["visible"]
            except Exception:  # noqa: BLE001
                logger.warning("Could not set Visible for %s!", app_type)

        if "display_alerts" in config and hasattr(app, "DisplayAlerts"):
            try:
                app.DisplayAlerts = config["display_alerts"]
            except Exception as e:  # noqa: BLE001
                logger.warning("Could not set DisplayAlerts for %s ! %s", app_type, e)

        logger.debug(
            f"Application {app_type.value} configured for background execution."
        )

    def _process_chunk(
        self, *, chunk: list[tuple[int, Path]], app_type: OfficeApp, out_dir: Path
    ) -> ConversionResult:
        chunk_res: ConversionResult = ConversionResult()

        pythoncom.CoInitialize()
        app = None
        try:
            app = self._get_app_instance(app_type=app_type)

            if app is None:
                raise RuntimeError(f"Could not initialize {app_type}.")
            self._disable_visibility(app=app, app_type=app_type)

            for idx, pf in chunk:
                self.check_stop()
                try:
                    processor = self._get_processor(app_type=app_type)
                    pdf_path = processor(app=app, file_path=pf, out_dir=out_dir)
                    chunk_res.success.append((idx, pdf_path))
                except Exception:
                    logger.exception("Failed to convert %s", pf)
                    chunk_res.failed.append((idx, pf))
                    continue
        except InterruptedError:
            raise
        except Exception:
            logger.exception("%s chunk error!", app_type)
            already_done = {item[0] for item in chunk_res.success} | {
                item[0] for item in chunk_res.failed
            }
            for idx, pf in chunk:
                if idx not in already_done:
                    chunk_res.failed.append((idx, pf))
        finally:
            self._safe_release_com_object(obj=app, app_type=app_type)
            app = None
            gc.collect()
            pythoncom.CoUninitialize()

        return chunk_res

    def _run_conversion(
        self, *, file_path: Path, conversion_func, out_dir: Path
    ) -> Path:
        """
        Universal wrapper for file conversion.
        """
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / file_path.with_suffix(".pdf").name
        output_path = get_unique_path(output_path)
        try:
            conversion_func(file_path.resolve(), output_path)
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        return output_path

    def _convert_pres_to_pdf(self, *, app, file_path: Path, out_dir: Path) -> Path:
        def action(input_path, output_path):
            pres = app.Presentations.Open(str(input_path), ReadOnly=True, WithWindow=0)
            try:
                pres.SaveAs(str(output_path), 32)
            finally:
                pres.Close()
                del pres

        return self._run_conversion(
            file_path=file_path, conversion_func=action, out_dir=out_dir
        )

    def _convert_table_to_pdf(self, *, app, file_path: Path, out_dir: Path) -> Path:
        def action(input_path, output_path):
            wb = app.Workbooks.Open(str(input_path), ReadOnly=True)
            try:
                self._prepare_table_for_export(wb=wb)
                wb.ExportAsFixedFormat(0, str(output_path))
            finally:
                wb.Close(SaveChanges=False)
                del wb

        return self._run_conversion(
            file_path=file_path, conversion_func=action, out_dir=out_dir
        )

    def _convert_doc_to_pdf(self, *, app, file_path: Path, out_dir: Path) -> Path:
        def action(input_path, output_path):
            doc = app.Documents.Open(
                str(input_path), ReadOnly=True, ConfirmConversions=False
            )
            try:
                doc.ExportAsFixedFormat(str(output_path), 17)
            finally:
                doc.Close(SaveChanges=0)
                del doc

        return self._run_conversion(
            file_path=file_path, conversion_func=action, out_dir=out_dir
        )

    def _safe_release_com_object(self, *, obj, app_type: str = "Office App"):
        """Safely closes the Office application and releases COM resources."""

        if obj:
            try:
                if hasattr(obj, "Quit"):
                    obj.Quit()
                logger.info(f"{app_type} closed successfully.")
            except Exception as e:  # noqa: BLE001
                logger.warning("Could not close %s gracefully: %s", app_type, e)
