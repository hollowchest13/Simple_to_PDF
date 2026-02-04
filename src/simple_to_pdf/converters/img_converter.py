import io
import logging
from pathlib import Path

from PIL import Image

from simple_to_pdf.converters.base_converter import BaseConverter
from simple_to_pdf.converters.models import ConversionResult

logger = logging.getLogger(__name__)


class ImageConverter(BaseConverter):
    SUPPORTED_FORMATS = {
        "image": {
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".gif",
            ".tiff",
            ".tif",
            ".webp",
            ".ppm",
            ".icns",
            ".ico",
            ".jfif",
            ".jpe",
            ".tga",
        }
    }

    def __init__(self, *, chunk_size: int = 30):
        super().__init__()
        self.chunk_size = chunk_size
        self.SUPPORTED_FORMATS = self.get_supported_formats()

    def convert_images_to_pdf(
        self, *, files: list[tuple[int, Path]]
    ) -> ConversionResult:
        all_results: ConversionResult = ConversionResult()
        for chunk in self.make_chunks(files, self.chunk_size):
            # Call the new method that handles one chunk
            chunk_res: ConversionResult = self._convert_images_chunk(chunk=chunk)
            all_results.successful.extend(chunk_res.successful)
            all_results.failed.extend(chunk_res.failed)
        return all_results

    def _convert_images_chunk(
        self, *, chunk: list[tuple[int, Path]]
    ) -> ConversionResult:
        """
        Converts a chunk of images to PDF format.
        Handles multi-page images (TIFF/GIF) and ensures RGB compatibility.
        """
        res: ConversionResult = ConversionResult()

        for idx, path in chunk:
            # Ensure path is a Path object
            path = Path(path)

            if not path.exists():
                logger.warning(f"⚠️ [{idx}] File not found: {path}")
                res.failed.append((idx, path))
                continue

            try:
                # Open the image file
                with Image.open(path) as img:
                    # Force loading to prevent 'closed file' errors during save
                    img.load()

                    frames = []
                    # Check for multiple frames (e.g., multi-page TIFFs or animated GIFs)
                    n_frames = getattr(img, "n_frames", 1)

                    for i in range(n_frames):
                        img.seek(i)
                        # Convert to RGB mode: mandatory for PDF format (removes alpha channel)
                        # Using .copy() ensures data remains in memory after file is closed
                        frame_rgb = img.convert("RGB")
                        frames.append(frame_rgb)

                    if frames:
                        buffer = io.BytesIO()
                        # Save the first frame as PDF and append others as additional pages
                        frames[0].save(
                            buffer,
                            format="PDF",
                            save_all=True,
                            append_images=frames[1:] if len(frames) > 1 else [],
                        )

                        pdf_data = buffer.getvalue()
                        if pdf_data:
                            res.successful.append((idx, pdf_data))

                        buffer.close()

                    # Explicitly close each frame object to free memory
                    for f in frames:
                        f.close()

            except Exception as e:
                res.failed.append((idx, path))
                logger.error(
                    f"❌ [{idx}] Image conversion error for {path.name}: {e}",
                    exc_info=True,
                )

        return res
