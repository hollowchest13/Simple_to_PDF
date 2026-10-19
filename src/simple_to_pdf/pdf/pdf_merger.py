import logging
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from simple_to_pdf.base_services.base import BaseService
from simple_to_pdf.utils.file_tools import get_unique_path

from .models import ConvertedFileItem, PageFormat, ProcessingReport

logger = logging.getLogger(__name__)


class PdfMerger(BaseService):
    def __init__(self):
        super().__init__()

    def _scale_and_append(
        self,
        *,
        reader: PdfReader,
        writer: PdfWriter,
        target_page_format: PageFormat | None = None,
    ):
        """
        Scales all pages from reader and adds them to writer.
        Correctly compensates for non-zero MediaBox origins to prevent left-side clipping.
        """
        if target_page_format is None:
            return
        base_w, base_h = target_page_format.size
        TOLERANCE = 1.0

        for source_page in reader.pages:
            box = source_page.mediabox
            scr_w = float(box.width)
            scr_h = float(box.height)

            orig_x = float(box.left)
            orig_y = float(box.bottom)

            is_landscape = scr_w > scr_h

            if is_landscape:
                target_w, target_h = max(base_w, base_h), min(base_w, base_h)
            else:
                target_w, target_h = min(base_h, base_w), max(base_h, base_w)

            is_correct_width = abs(scr_w - target_w) < TOLERANCE
            is_correct_height = abs(scr_h - target_h) < TOLERANCE

            if is_correct_width and is_correct_height and orig_x == 0 and orig_y == 0:
                writer.add_page(source_page)
                continue

            canvas = PageObject.create_blank_page(width=target_w, height=target_h)
            scale = min(target_w / scr_w, target_h / scr_h)
            tx = (target_w - scr_w * scale) / 2 - (orig_x * scale)
            ty = (target_h - scr_h * scale) / 2 - (orig_y * scale)

            transformation = Transformation().scale(scale, scale).translate(tx, ty)

            canvas.merge_transformed_page(source_page, transformation)
            writer.add_page(canvas)

    def merge_to_pdf(
        self,
        *,
        conversion_rep: ProcessingReport,
        target_page_format: PageFormat | None = None,
        output_path: Path,
    ) -> Path:
        """Merges multiple files into a single PDF and saves it directly to the output path."""

        pdf_path_list: list[ConvertedFileItem] = conversion_rep.documents
        self._files_count = len(pdf_path_list)

        stage_name = "merging"

        self._show_callback(
            "progress",
            {
                "stage": stage_name,
                "mode": "indeterminate",
            },
        )

        if not pdf_path_list:
            raise ValueError("No valid PDF data to merge")

        pdf_path_list.sort(key=lambda doc: doc.index)

        writer = PdfWriter()
        success = 0
        failed = conversion_rep.failed  # загальна кількість невдач, для звіту
        merge_failed = 0  # лише помилки цього етапу
        total_to_merge = len(pdf_path_list)
        try:
            for i, doc_item in enumerate(pdf_path_list, start=1):
                self.check_stop()
                file_path = doc_item.converted_path
                filename = file_path.name

                try:
                    reader = PdfReader(file_path)
                    if target_page_format is None:
                        writer.append(reader)
                    else:
                        self._scale_and_append(
                            reader=reader,
                            writer=writer,
                            target_page_format=target_page_format,
                        )
                except Exception:
                    logger.exception("Failed to process %s!", filename)
                    failed += 1
                    merge_failed += 1
                    self._show_callback(
                        "status",
                        {
                            "key": f"{stage_name}.error.unknown",
                            "status": "warning",
                            "path": file_path,
                        },
                    )
                finally:
                    self._show_callback(
                        "progress",
                        {
                            "stage": stage_name,
                            "mode": "determinate",
                            "current": i,
                            "filename": filename,
                            "total": total_to_merge,
                        },
                    )
            if len(writer.pages) == 0:
                raise ValueError("No PDF data")
            self.check_stop()
            output_path = get_unique_path(output_path)
            writer.write(output_path)
            success = total_to_merge - merge_failed
            return output_path
        except InterruptedError:
            logger.info(f"{stage_name} successfully cancelled by the user.")
            raise
        finally:
            self._show_callback(
                "status",
                {
                    "key": f"{stage_name}.done",
                    "status": "info",
                    "success": success,
                    "failed": failed,
                },
            )
            writer.close()
