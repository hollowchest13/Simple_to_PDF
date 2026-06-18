import logging
from pathlib import Path

from simple_to_pdf.converters import ConverterFactory
from simple_to_pdf.converters.models import ConversionResult
from simple_to_pdf.pdf.models import BytePdfDocument, ProcessingReport

logger = logging.getLogger(__name__)


class ConversionService:
    def __init__(self):
        factory = ConverterFactory()
        self.converter = factory.get_converter()
        self._callback = lambda *args, **kwargs: None

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    def get_pdfs_data(self, files: list[tuple[int, Path]]) -> ProcessingReport:
        pdf_data_list: list[BytePdfDocument] = []
        to_conversion = []

        success = 0
        failed = 0

        for idx, path in files:
            if self.converter.is_pdf_file(file_path=path):
                pdf_data_list.append(
                    BytePdfDocument(
                        index=idx, data=path.read_bytes(), original_path=path
                    )
                )
            elif self.converter.needs_conversion(file_path=path):
                to_conversion.append((idx, path))

        if to_conversion:
            stage_name = "converting"
            self.callback(
                "progress",
                **{
                    "stage": stage_name,
                    "mode": "indeterminate",
                },
            )
            paths_by_idx = {file_idx: path for file_idx, path in files}
            try:
                conversion_res: ConversionResult = self.converter.convert_to_pdf(
                    files=to_conversion,
                )
            except InterruptedError:
                logger.info(f"{stage_name} process was interrupted by user.")
                raise

            success = len(conversion_res.success)
            failed = len(conversion_res.failed)

            converted_docs = [
                BytePdfDocument(
                    index=idx, data=pdf_data, original_path=paths_by_idx[idx]
                )
                for idx, pdf_data in conversion_res.success
            ]
            pdf_data_list.extend(converted_docs)
            self.callback(
                "progress",
                **{
                    "stage": stage_name,
                    "mode": "determinate",
                    "current": 1,
                    "total": 1,
                },
            )
            self.callback(
                "status",
                **{
                    "key": f"{stage_name}.done",
                    "status": "info" if failed == 0 else "warning",
                    "success": success,
                    "failed": failed,
                },
            )
            for failed_path in conversion_res.failed:
                self.callback(
                    "status",
                    **{
                        "key": f"{stage_name}.error.unknown",
                        "status": "error",
                        "path": str(failed_path[1]),
                        "error": "Office application failed to process this document",
                    },
                )
        return ProcessingReport(documents=pdf_data_list, success=success, failed=failed)
