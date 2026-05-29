import io
import logging
from typing import List

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from .models import BytePdfDocument, PageFormat, ProcessingReport

logger = logging.getLogger(__name__)


class PdfMerger:
    def __init__(self):
        self._callback = lambda *args, **kwargs: None

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    def _scale_and_append(
        self,
        *,
        reader: PdfReader,
        writer: PdfWriter,
        target_page_format: PageFormat|None=None,
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
        target_page_format: PageFormat|None=None,
    ) -> bytes:
        """Merges multiple files into a single PDF and returns original bytes if it is single PDF."""

        pdf_data_list: List[BytePdfDocument] = conversion_rep.documents
        self._files_count = len(pdf_data_list)

        stage_name = "merging"

        self._show_callback(
            "progress",
            {
                "stage": stage_name,
                "mode": "indeterminate",
            },
        )

        if not pdf_data_list:
            raise ValueError("No valid PDF data to merge")

        pdf_data_list.sort(key=lambda doc: doc.index)

        writer = PdfWriter()
        active_streams: list[io.BytesIO] = []
        success = 0
        failed = conversion_rep.failed
        total_to_merge = len(pdf_data_list)
        try:
            for i, pdf_data in enumerate(pdf_data_list, start=1):
                file_path = pdf_data.original_path
                filename = file_path.name

                try:
                    pdf_stream = io.BytesIO(pdf_data.data)
                    active_streams.append(pdf_stream)
                    reader = PdfReader(pdf_stream)
                    if target_page_format is None:
                        writer.append(reader)
                    else:
                        self._scale_and_append(
                            reader=reader,
                            writer=writer,
                            target_page_format=target_page_format,
                        )
                except Exception as e:
                    logger.error(f"Failed to process {filename}: {e}", exc_info=True)
                    failed += 1
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

            with io.BytesIO() as pdf_buffer:
                writer.write(pdf_buffer)
                pdf_bytes = pdf_buffer.getvalue()
            success = total_to_merge - failed
            return pdf_bytes
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
            for stream in active_streams:
                stream.close()
            active_streams.clear()
            writer.close()

    def _show_callback(self, event_type: str, data: dict, force: bool = False):
        if force or self.should_show_callback():
            self.callback(event_type, **data)

    def should_show_callback(self) -> bool:
        return self._files_count > 1
