import logging
from pathlib import Path

from simple_to_pdf.base_services.base import BaseService
from simple_to_pdf.converters import ConverterFactory
from simple_to_pdf.converters.models import ConversionResult
from simple_to_pdf.pdf.models import ConvertedFileItem, ProcessingReport

logger = logging.getLogger(__name__)


class ConversionService(BaseService):
    def __init__(self):
        super().__init__()
        factory = ConverterFactory()
        self.converter = factory.get_converter()

    def get_conversion_rep(
        self, files: list[tuple[int, Path]], out_dir: Path
    ) -> ProcessingReport:
        logger.info("files=%s", [(i, str(p), p.suffix) for i, p in files])
        conversion_list: list[ConvertedFileItem] = []
        to_conversion = []

        success = 0
        failed = 0

        for idx, path in files:
            if self.converter.is_pdf_file(file_path=path):
                conversion_list.append(
                    ConvertedFileItem(
                        index=idx, converted_path=path, original_path=path
                    )
                )
            elif self.converter.needs_conversion(file_path=path):
                to_conversion.append((idx, path))

        if to_conversion:
            stage_name = "converting"
            self.callback(
                "progress",
                stage=stage_name,
                mode="indeterminate",
            )
            paths_by_idx = {file_idx: path for file_idx, path in files}
            try:
                conversion_res: ConversionResult = self.converter.convert_to_pdf(
                    files=to_conversion, out_dir=out_dir
                )
            except InterruptedError:
                logger.info(f"{stage_name} process was interrupted by user.")
                raise

            success = len(conversion_res.success)
            failed = len(conversion_res.failed)

            converted_docs = [
                ConvertedFileItem(
                    index=idx,
                    converted_path=converted_path,
                    original_path=paths_by_idx[idx],
                )
                for idx, converted_path in conversion_res.success
            ]
            conversion_list.extend(converted_docs)
            self.callback(
                "progress",
                stage=stage_name,
                mode="determinate",
                current=1,
                total=1,
            )
            self.callback(
                "status",
                key=f"{stage_name}.done",
                status="info" if failed == 0 else "warning",
                success=success,
                failed=failed,
            )
            for failed_path in conversion_res.failed:
                self.callback(
                    "status",
                    key=f"{stage_name}.error.unknown",
                    status="error",
                    path=str(failed_path[1]),
                    error="Office application failed to process this document",
                )
        logger.info(
            "documents=%d success=%d failed=%d", len(conversion_list), success, failed
        )
        return ProcessingReport(
            documents=conversion_list, success=success, failed=failed
        )
