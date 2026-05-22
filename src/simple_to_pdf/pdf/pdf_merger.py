import io
import logging
from pathlib import Path
from typing import List

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from simple_to_pdf.converters import ConverterFactory

from .models import PageFormat, ProcessingResult

logger = logging.getLogger(__name__)


class PdfMerger:
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

    def _get_pdfs_bytes(self, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        """Prepares PDF bytes, converting non-PDF files if necessary."""

        pdf_bytes = []
        to_conversion = []

        for idx, path in files:
            path = path
            if not path.exists():
                continue
            if self.converter.is_pdf_file(file_path=path):
                pdf_bytes.append((idx, path.read_bytes()))
            elif self.converter.needs_conversion(file_path=path):
                to_conversion.append((idx, path))

        if to_conversion:
            # Start indeterminate progress for conversion stage

            self.callback(
                "progress",
                **{
                    "stage": "converting",
                    "mode": "indeterminate",
                },
            )
            # Bulk conversion
            conversion_res = self.converter.convert_to_pdf(files=to_conversion)
            pdf_bytes.extend(conversion_res.success)
            pdf_bytes.sort(key=lambda x: x[0])
            self.callback(
                "progress",
                **{
                    "stage": "converting",
                    "mode": "determinate",
                    "current": len(to_conversion),
                    "total": len(to_conversion),
                },
            )
            self.callback(
                "status",
                **{
                    "key": "convert.done",
                    "status": "info" if len(conversion_res.failed) == 0 else "warning",
                    "success": len(conversion_res.success),
                    "failed": len(conversion_res.failed),
                },
            )
            for failed_path in conversion_res.failed:
                self.callback(
                    "status",
                    **{
                        "key": "convert.error",
                        "status": "error",
                        "path": str(failed_path[1]),
                        "error": "Office application failed to process this document",
                    },
                )
        return pdf_bytes

    def _scale_and_append(
        self,
        *,
        reader: PdfReader,
        writer: PdfWriter,
        target_page_format: PageFormat = PageFormat.A4,
    ):
        """
        Scales all pages from reader and adds them to writer.
        Correctly compensates for non-zero MediaBox origins to prevent left-side clipping.
        """
        target_w, target_h = target_page_format.size
        TOLERANCE = 1.0

        for source_page in reader.pages:
            box = source_page.mediabox
            scr_w = float(box.width)
            scr_h = float(box.height)

            orig_x = float(box.left)
            orig_y = float(box.bottom)

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
        files: List[tuple[int, Path]],
        target_page_format: PageFormat = PageFormat.A4,
    ) -> ProcessingResult:
        """Merges multiple files into a single PDF."""

        files_sorted = sorted(files, key=lambda x: x[0])
        paths_by_idx = {file_idx: path for file_idx, path in files_sorted}

        pdfs_bytes_list = self._get_pdfs_bytes(files_sorted)
        if not pdfs_bytes_list:
            raise ValueError("No valid PDF data to merge")

        writer = PdfWriter()
        active_streams: list[io.BytesIO] = []

        failed = len(files_sorted) - len(pdfs_bytes_list)
        total_to_merge = len(files_sorted)
        try:
            for i, (idx, pdf_data) in enumerate(pdfs_bytes_list, start=1):
                filename = paths_by_idx[idx].name
                try:
                    pdf_stream = io.BytesIO(pdf_data)
                    active_streams.append(pdf_stream)
                    reader = PdfReader(pdf_stream)
                    self._scale_and_append(
                        reader=reader,
                        writer=writer,
                        target_page_format=target_page_format,
                    )
                except Exception as e:
                    logger.error(f"Failed to process {filename}: {e}", exc_info=True)
                    failed += 1
                finally:
                    self.callback(
                        "progress",
                        **{
                            "stage": "merging",
                            "mode": "determinate",
                            "current": i,
                            "filename": filename,
                            "total": total_to_merge,
                        },
                    )

            if len(writer.pages) == 0:
                raise ValueError(
                    "Unable to process the document. The file might be corrupted, or the system conversion service is temporarily unavailable. Please try again or contact support"
                )

            with io.BytesIO() as pdf_buffer:
                writer.write(pdf_buffer)
                pdf_bytes = pdf_buffer.getvalue()
            success = total_to_merge - failed
            return ProcessingResult(success, failed, pdf_bytes)
        finally:
            for stream in active_streams:
                stream.close()
            active_streams.clear()
            writer.close()
