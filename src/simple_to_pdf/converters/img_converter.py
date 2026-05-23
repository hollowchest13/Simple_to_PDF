import io
import logging
from pathlib import Path

from PIL import Image, ImageOps

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
        super().__init__(chunk_size=chunk_size)
        self.SUPPORTED_FORMATS = self.get_supported_formats()

    def convert_to_pdf(self, *, files: list[tuple[int, Path]]) -> ConversionResult:
        return self._convert_images_to_pdf(files=files)

    def _convert_images_to_pdf(
        self, *, files: list[tuple[int, Path]]
    ) -> ConversionResult:
        all_results: ConversionResult = ConversionResult()
        for chunk in self.make_chunks(files, self.chunk_size):
            chunk_res: ConversionResult = self._convert_images_chunk(chunk=chunk)
            all_results.success.extend(chunk_res.success)
            all_results.failed.extend(chunk_res.failed)
        return all_results

    def _convert_single_image(self, path: Path) -> bytes | None:
        """Convert a single image file (including multi-page images) to PDF data."""
        MAX_SIZE = 2500
        if not path.exists():
            return None

        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            if max(img.size) > MAX_SIZE:
                img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
            img.load()
            frames = []
            n_frames = getattr(img, "n_frames", 1)

            for i in range(n_frames):
                img.seek(i)
                frame_rgb = img.convert("RGB")
                frames.append(frame_rgb)

            if not frames:
                return None

            with io.BytesIO() as buffer:
                try:
                    frames[0].save(
                        buffer,
                        format="PDF",
                        save_all=True,
                        append_images=frames[1:] if len(frames) > 1 else [],
                    )
                    return buffer.getvalue()
                finally:
                    for f in frames:
                        f.close()

    def _convert_images_chunk(
        self, *, chunk: list[tuple[int, Path]]
    ) -> ConversionResult:
        """Process a chunk using the single-image conversion method."""
        res = ConversionResult()

        for idx, path in chunk:
            path = Path(path)
            try:
                pdf_data = self._convert_single_image(path)

                if pdf_data:
                    res.success.append((idx, pdf_data))
                else:
                    logger.warning(f"⚠️ [{idx}] File not found or empty: {path}")
                    res.failed.append((idx, path))

            except Exception as e:
                logger.error(f"[{idx}] Error converting {path.name}: {e}")
                res.failed.append((idx, path))

        return res
