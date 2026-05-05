import io
import logging
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from simple_to_pdf.converters import ConverterFactory

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

    def merge_to_pdf(
        self, *, files: list[tuple[int, str]], output_path: str | Path, callback=None
    ) -> Path:
        """Merges multiple files into a single PDF."""
        # Sort and create lookup for filenames
        files_sorted = sorted(files, key=lambda x: x[0])
        names_lookup = {idx: name for idx, name in files_sorted}

        # Step 1: Get PDF bytes (includes potential conversion)
        pdfs_sorted = self._get_pdfs_bytes(files_sorted, callback=callback)

        # Step 2: Merge
        writer = PdfWriter()

        for i, (idx, pdf_data) in enumerate(pdfs_sorted, 1):
            full_path = Path(names_lookup.get(idx, f"File {idx}")).resolve()
            filename = full_path.name
            try:
                reader = PdfReader(io.BytesIO(pdf_data))
                writer.append(reader)

                if callback:
                    callback(
                        "progress",
                        **{
                            "stage": "merging",
                            "mode": "determinate",
                            "current": i,
                            "filename": filename,
                        },
                    )
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}", exc_info=True)
                if callback:
                    callback(
                        "status",
                        **{
                            "key": "merge.error",
                            "status": "error",
                            "path": str(full_path),
                        },
                    )

        if len(writer.pages) == 0:
            raise RuntimeError("No pages were added. Check input files.")

        # Save result
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("wb") as f:
            writer.write(f)

        if callback:
            callback(
                "status",
                **{"key": "merge.done", "status": "info", "path": str(output_file)},
            )
        return output_file
