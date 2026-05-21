import io
import logging
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
        self._callback = lambda *args, **kwargs: None

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    def _get_pix_info(self, pix: pymupdf.Pixmap) -> PixInfo:
        if pix.n != 3 or pix.alpha != 0:
            pix_rgb = pymupdf.Pixmap(pymupdf.csRGB, pix)
            samples = pix_rgb.samples
            width, height = pix_rgb.width, pix_rgb.height
            del pix_rgb
        else:
            samples = pix.samples
            width, height = pix.width, pix.height

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
                logger.debug(
                    f"Skipped image {xref} due to colorspace: {pix.colorspace.name}"
                )
                return

            pix_info = self._get_pix_info(pix)

            with Image.frombytes(
                "RGB", (pix_info.width, pix_info.height), pix_info.samples
            ) as pil_img:
                with io.BytesIO() as buffer:
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

        except Exception as e:
            logger.debug(f"Image compressing failed {xref}: {e}")
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
        pdf_bytes: bytes,
        quality: int = 20,
    ) -> bytes:
        """Main method that accepts PDF bytes, compresses the PDF, and returns new bytes.

        Args:
            pdf_bytes (bytes): Bytes of the original PDF file.
            callback (Callable, optional): Callback function to update progress in the
                CustomTkinter GUI. Accepts message type and keyword arguments.
            quality (int): Desired image quality after compression (1 to 100). Default: 75.

        Returns:
            bytes: Bytes of the compressed PDF (or original bytes if failed).
        """
        if not pdf_bytes:
            logger.warning("Received empty bytes for compression")
            return pdf_bytes

        try:
            with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
                total_pages = len(doc)

                if total_pages == 0:
                    return pdf_bytes

                processed_xrefs = set()

                for idx in range(total_pages):
                    page = doc[idx]
                    self._set_page_images_quality(
                        page, doc=doc, quality=quality, processed_xrefs=processed_xrefs
                    )
                    self.callback(
                        "progress",
                        **{
                            "stage": "compressing",
                            "mode": "determinate",
                            "current": idx + 1,
                            "total": total_pages,
                        },
                    )

                self.callback(
                    "progress",
                    **{
                        "stage": "saving",
                        "mode": "indeterminate",
                    },
                )

                compressed_stream = io.BytesIO()
                doc.save(
                    compressed_stream,
                    garbage=self.garbage_level,
                    deflate=self.deflate,
                    clean=self.clean,
                )
                self.callback(
                    "progress",
                    **{
                        "stage": "saving",
                        "mode": "determinate",
                        "current": total_pages,
                        "total": total_pages,
                    },
                )
                self.callback(
                    "status",
                    **{
                        "key": "compress.done",
                        "status": "info",
                    },
                )
                return compressed_stream.getvalue()

        except Exception as e:
            logger.error(f"Compressing error: {e}", exc_info=True)
            self.callback(
                "status",
                **{
                    "key": "compress.error",
                    "status": "error",
                },
            )
            return pdf_bytes
