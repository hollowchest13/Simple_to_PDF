import io
import logging
from pathlib import Path

import pymupdf
from PIL import Image

from simple_to_pdf.base_services.base import BaseService

from .models import PixInfo

logger = logging.getLogger(__name__)


class CompressingError(Exception):
    """Exception thrown when the PDF failed to compress."""


class PDFCompressor(BaseService):
    """A class to compress PDF files by optimizing embedded images.

    This class utilizes the PyMuPDF library to parse the PDF structure
    and the Pillow (PIL) library to compress raster images, significantly
    reducing the final file size.
    """

    def __init__(
        self, *, garbage_level: int = 4, deflate: bool = True, clean: bool = True
    ):
        """Initializes the compressor with PDF saving configurations.

        Args:
            garbage_level (int): Garbage collection level during saving (1 to 4).
                Level 4 ensures maximum cleanup of unused objects.
            deflate (bool): Whether to compress data streams (text, fonts, etc.) using ZIP.
            clean (bool): Whether to clean and optimize the internal file structure.
        """
        super().__init__()
        self.garbage_level = garbage_level
        self.deflate = deflate
        self.clean = clean

    def _get_pix_info(self, pix: pymupdf.Pixmap) -> PixInfo | None:
        if pix.colorspace is None:
            return None

        try:
            if pix.n != 3 or pix.alpha != 0:
                pix_rgb = pymupdf.Pixmap(pymupdf.csRGB, pix)
                samples = pix_rgb.samples
                width, height = pix_rgb.width, pix_rgb.height
                del pix_rgb
            else:
                samples = pix.samples
                width, height = pix.width, pix.height
        except Exception:
            logger.warning("Could not convert pixmap to RGB colorspace")
            raise

        return PixInfo(samples=samples, width=width, height=height)

    def _compress_single_image(
        self, *, page: pymupdf.Page, doc: pymupdf.Document, xref: int, quality: int
    ) -> None:
        pix = None
        try:
            img_info = doc.extract_image(xref)
            if not img_info:
                return
            orig_bytes = img_info["image"]
            pix = pymupdf.Pixmap(doc, xref)

            if pix.colorspace and pix.colorspace.name in ("DeviceCMYK", "Indexed"):
                return

            pix_info = self._get_pix_info(pix)
            if pix_info is None:
                return

            with (
                Image.frombytes(
                    "RGB", (pix_info.width, pix_info.height), pix_info.samples
                ) as pil_img,
                io.BytesIO() as buffer,
            ):
                pil_img.save(
                    buffer,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                    progressive=True,
                )
                compressed_jpeg_bytes = buffer.getvalue()

            if len(compressed_jpeg_bytes) < len(orig_bytes):
                page.replace_image(xref, stream=compressed_jpeg_bytes)
                logger.debug(
                    f"Image {xref} compressed: {len(orig_bytes)} -> {len(compressed_jpeg_bytes)} bytes"
                )
            else:
                logger.debug(
                    f"Skipped image {xref}: compressed size is larger than original"
                )

        except Exception:
            logger.exception(f"Image compressing failed {xref}!")
        finally:
            if pix is not None:
                del pix

    def _set_page_images_quality(
        self,
        page: pymupdf.Page,
        *,
        doc: pymupdf.Document,
        quality: int,
        processed_xrefs: set[int],
    ) -> None:
        """Finds and compresses all images on a specific PDF page.

        Extracts each image on the page as a Pixmap, converts it to Pillow,
        compresses it as a JPEG with the specified quality, and writes it back.

        Args:
            page (pymupdf.Page): The PDF page object containing images to compress.
            doc (pymupdf.Document): The PDF document object the page belongs to.
            quality (int): Image quality level for Pillow (1 to 100).
            processed_xrefs(set): Processed image xref to avoid image multiple comressing.
        """

        try:
            image_list = page.get_images(full=True)
        except Exception:
            logger.exception("page.get_image error!")
            image_list = []

        for img in image_list:
            self.check_stop()

            xref = img[0]
            if xref not in processed_xrefs:
                self._compress_single_image(
                    page=page, doc=doc, xref=xref, quality=quality
                )
                processed_xrefs.add(xref)

    def compress(
        self, *, input_pdf_path: Path, quality: int = 20, output_path: Path
    ) -> Path:
        """Main method that accepts PDF bytes, compresses the PDF, and returns new bytes.

        Args:
            pdf_bytes (bytes): Bytes of the original PDF file.
            callback (Callable, optional): Callback function to update progress in the
                CustomTkinter GUI. Accepts message type and keyword arguments.
            quality (int): Desired image quality after compression (1 to 100). Default: 75.

        Returns:
            Path: Path to the compressed PDF (or input_path if failed).
        """
        total_pages: int = 0
        stage_name: str = "compressing"
        current_stage: str = stage_name

        if not input_pdf_path:
            logger.warning("Received empty bytes for compression")
            return input_pdf_path

        self._show_callback(
            "progress", {"stage": current_stage, "mode": "indeterminate"}, force=True
        )
        try:
            with pymupdf.open(input_pdf_path) as doc:
                total_pages = len(doc)

                if total_pages == 0:
                    raise ValueError(
                        f"The PDF file contains no pages: {input_pdf_path}"
                    )

                processed_xrefs = set()

                for idx in range(total_pages):
                    self.check_stop()

                    page = doc[idx]
                    if self.is_hard_page(page=page):
                        continue
                    self._set_page_images_quality(
                        page, doc=doc, quality=quality, processed_xrefs=processed_xrefs
                    )
                    self._show_callback(
                        "progress",
                        {
                            "stage": current_stage,
                            "mode": "determinate",
                            "current": idx + 1,
                            "total": total_pages,
                        },
                        force=True,
                    )

                current_stage = "processing"
                self._show_callback(
                    "progress",
                    {"stage": current_stage, "mode": "indeterminate"},
                    force=True,
                )
                doc.save(
                    output_path,
                    garbage=self.garbage_level,
                    deflate=self.deflate,
                    clean=self.clean,
                )

                self._show_callback(
                    "status",
                    {"key": f"{stage_name}.done", "status": "info"},
                    force=True,
                )
                return output_path
        except InterruptedError:
            logger.info(f"{stage_name} process was interrupted by user.")
            raise
        except Exception:
            logger.exception("Compressing error!")
            self._show_callback(
                "status",
                {"key": "compressing.error.critical", "status": "error"},
                force=True,
            )
            return input_pdf_path

    def is_hard_page(self, *, page) -> bool:
        try:
            drawings = page.get_drawings()
            return len(drawings) > 1000
        except Exception:
            logger.exception("Page parsing error!")
            return False
