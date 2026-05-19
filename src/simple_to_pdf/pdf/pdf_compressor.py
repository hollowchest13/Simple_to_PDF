import io
import logging
from typing import Any, Callable, Optional
from .models import PixInfo

import pymupdf
from PIL import Image

logger = logging.getLogger(__name__)


class PDFCompressor:
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

        self.garbage_level = garbage_level
        self.deflate = deflate
        self.clean = clean

    def _get_pix_info(self, pix: pymupdf.Pixmap) -> PixInfo:
        if pix.n != 3 or pix.alpha != 0:
            pix_rgb = pymupdf.Pixmap(pymupdf.csRGB, pix)
            samples = pix_rgb.samples
            width, height = pix_rgb.width, pix_rgb.height
        else:
            samples = pix.samples
            width, height = pix.width, pix.height
        return PixInfo(samples=samples, width=width, height=height)

    def _compress_single_image(
        self, *, page: pymupdf.Page, doc: pymupdf.Document, xref: int, quality: int
    ) -> None:
        pix = None
        pix_rgb = None
        try:
            pix = pymupdf.Pixmap(doc, xref)
            pix_info = self._get_pix_info(pix)
            with Image.frombytes(
                "RGB", (pix_info.width, pix_info.height), pix_info.samples
            ) as pil_img:
                with io.BytesIO() as buffer:
                    pil_img.save(buffer, format="JPEG", quality=quality)
                    compressed_jpeg_bytes = buffer.getvalue()
            page.replace_image(xref, stream=compressed_jpeg_bytes)

        except Exception as e:
            logger.debug(f"Image compressing failed {xref}: {e}")
        finally:
            if pix:
                del pix
            if pix_rgb:
                del pix_rgb

    def _set_page_images_quality(
        self,
        page: pymupdf.Page,
        *,
        doc: pymupdf.Document,
        quality: int,
        processed_xrefs: set,
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
            image_list = []

        for img in image_list:
            xref = img[0]
            if xref not in processed_xrefs:
                self._compress_single_image(
                    page=page, doc=doc, xref=xref, quality=quality
                )
                processed_xrefs.add(xref)

    def compress(
        self,
        *,
        pdf_bytes: io.BytesIO,
        callback: Optional[Callable[..., Any]],
        quality: int = 75,
    ) -> io.BytesIO:
        """Main method that accepts PDF bytes, compresses the PDF, and returns new bytes.

        Args:
            pdf_bytes (io.BytesIO): Byte stream of the original PDF file.
            callback (Callable, optional): Callback function to update progress in the
                CustomTkinter GUI. Accepts message type and keyword arguments.
            quality (int): Desired image quality after compression (1 to 100). Default: 75.

        Returns:
            io.BytesIO: Byte stream of the compressed PDF (or original stream if failed).
        """
        try:
            pdf_bytes.seek(0)
            doc = pymupdf.open(stream=pdf_bytes.read(), filetype="pdf")
            total_pages = len(doc)

            if total_pages == 0:
                pdf_bytes.seek(0)
                return pdf_bytes

            processed_xrefs = set()

            for idx in range(total_pages):
                page = doc[idx]
                self._set_page_images_quality(
                    page, doc=doc, quality=quality, processed_xrefs=processed_xrefs
                )

                if callback:
                    callback(
                        "progress",
                        **{
                            "stage": "compressing",
                            "mode": "determinate",
                            "current": idx,
                            "total": total_pages,
                        },
                    )

            compressed_stream = io.BytesIO()
            doc.save(
                compressed_stream,
                garbage=self.garbage_level,
                deflate=self.deflate,
                clean=self.clean,
            )
            doc.close()
            compressed_stream.seek(0)
            if callback:
                callback(
                    "status",
                    **{
                        "key": "compress.done",
                        "status": "info",
                    },
                )
            return compressed_stream

        except Exception as e:
            logger.error(f"Compressing error: {e}", exc_info=True)
            pdf_bytes.seek(0)
            return pdf_bytes
