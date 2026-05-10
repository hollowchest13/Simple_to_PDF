import io
import logging
from pathlib import Path
from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from simple_to_pdf.converters import ConverterFactory
from .models import PageFormat

logger = logging.getLogger(__name__)


class PdfMerger:
    def __init__(self):
        factory = ConverterFactory()
        self.converter = factory.get_converter()

    def _get_pdfs_bytes(
        self, files: list[tuple[int, str]], callback=None
    ) -> list[tuple[int, bytes]]:
        """Prepares PDF bytes, converting non-PDF files if necessary."""
        pdf_bytes = []
        to_conversion = []

        for idx, path_str in files:
            path = Path(path_str)
            if not path.exists():
                continue
            if self.converter.is_pdf_file(file_path=path):
                pdf_bytes.append((idx, path.read_bytes()))
            elif self.converter.needs_conversion(file_path=path):
                to_conversion.append((idx, path))

        if callback and to_conversion:
            # Start indeterminate progress for conversion stage

            callback(
                "progress",
                **{
                    "stage": "converting",
                    "mode": "indeterminate",
                    "total": len(files),
                },
            )

            # Bulk conversion
            conversion_res = self.converter.convert_to_pdf(files=to_conversion)

            callback(
                "progress",
                **{
                    "stage": "converting",
                    "mode": "determinate",
                    "current": len(to_conversion),
                    "total": len(to_conversion),
                },
            )
            pdf_bytes.extend(conversion_res.successful)
            pdf_bytes.sort(key=lambda x: x[0])
            callback(
                "progress",
                **{
                    "stage": "converting",
                    "mode": "determinate",
                    "current": len(to_conversion),
                    "total": len(to_conversion),
                },
            )
            callback(
                "status",
                **{
                    "key": "convert.done",
                    "status": "info" if len(conversion_res.failed) == 0 else "warning",
                    "success": len(conversion_res.successful),
                    "failed": len(conversion_res.failed),
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
        """Scale all pages from readers and adds them to writer
        If a page already matches the target page format, it is added directly to to preserve metadata"""

        target_w, target_h = target_page_format.size
        # Define a small tolerance (1 point = ~0.35mm) to account for float inaccuracies
        TOLERANCE = 1.0

        for source_page in reader.pages:
            scr_w = float(source_page.mediabox.width)
            scr_h = float(source_page.mediabox.height)

            # Check if the page size already matches the target format
            is_correct_width = abs(scr_w - target_w) < TOLERANCE
            is_correct_height = abs(scr_h - target_h) < TOLERANCE

            if is_correct_width and is_correct_height:
                writer.add_page(source_page)
            else:
                canvas = PageObject.create_blank_page(width=target_w, height=target_h)
                scale = min(target_w / scr_w, target_h / scr_h)
                tx = (target_w - scr_w * scale) / 2
                ty = (target_h - scr_h * scale) / 2
                transformation = Transformation().scale(scale, scale).translate(tx, ty)
                canvas.merge_transformed_page(source_page, transformation)
                writer.add_page(canvas)

    def merge_to_pdf(
        self,
        *,
        files: list[tuple[int, str]],
        output_path: str | Path,
        target_page_format: PageFormat = PageFormat.A4,
        callback=None,
    ) -> Path:
        """Merges multiple files into a single PDF."""

        # Sort and create lookup for filenames
        files_sorted = sorted(files, key=lambda x: x[0])
        names_lookup = {idx: name for idx, name in files_sorted}

        # Step 1: Get PDF bytes (includes potential conversion)
        pdfs_sorted = self._get_pdfs_bytes(files_sorted, callback=callback)

        # Step 2: Merge
        writer = PdfWriter()
        failed = 0
        total = len(files_sorted)

        for i, (idx, pdf_data) in enumerate(pdfs_sorted, 1):
            full_path = Path(names_lookup.get(idx, f"File {idx}")).resolve()
            filename = full_path.name
            try:
                reader = PdfReader(io.BytesIO(pdf_data))
                self._scale_and_append(
                    reader=reader, writer=writer, target_page_format=target_page_format
                )
                if callback:
                    callback(
                        "progress",
                        **{
                            "stage": "merging",
                            "mode": "determinate",
                            "current": i,
                            "filename": str(filename),
                            "total": total,
                        },
                    )
            except Exception as e:
                logger.error(f"ERROR: Failed to process {filename}: {e}", exc_info=True)
                if callback:
                    callback(
                        "status",
                        **{
                            "key": "merge.error",
                            "status": "error",
                            "path": str(full_path),
                        },
                    )
                failed += 1

        if len(writer.pages) == 0:
            raise RuntimeError("No pages were added. Check input files.")

        # Save result
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("wb") as f:
            writer.write(f)

        success = total - failed

        if callback:
            callback(
                "status",
                **{
                    "key": "merge.done",
                    "status": "info",
                    "success": str(success),
                    "failed": str(failed),
                    "path": str(output_file),
                },
            )
        return output_file
