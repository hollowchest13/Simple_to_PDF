import io
import logging
from typing import Any, Callable, Dict, Optional

import pymupdf
from PIL import Image

logger = logging.getLogger(__name__)


class PDFCompressor:
    def __init__(
        self, *, garbage_level: int = 4, deflate: bool = True, clean: bool = True
    ):
        self.garbage_level = garbage_level
        self.deflate = deflate
        self.clean = clean

    def _set_page_images_quality(
        self, page: pymupdf.Page, *, doc: pymupdf.Document, quality: int
    ) -> None:
        """
        Стискає зображення на сторінці, використовуючи Pillow для керування якістю.
        Працює на будь-яких версіях PyMuPDF.
        """
        try:
            image_list = page.get_images(full=True)
        except Exception:
            return

        for img in image_list:
            xref = img[0]
            try:
                # 1. Отримуємо сирі пікселі з PDF за допомогою PyMuPDF
                pix = pymupdf.Pixmap(doc, xref)

                # Якщо це маска або специфічний формат (alpha-канал), конвертуємо в базовий RGB
                if pix.n != 3 or pix.alpha != 0:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

                # 2. Перетворюємо Pixmap в об'єкт зображення Pillow за допомогою сирих байтів (samples)
                pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                # 3. Стискаємо картинку в пам'яті через Pillow з потрібною якістю
                buffer = io.BytesIO()
                # Ось тут якість (quality) працює ідеально!
                pil_img.save(buffer, format="JPEG", quality=quality)
                compressed_jpeg_bytes = buffer.getvalue()

                # 4. Записуємо стиснуті байти назад у PDF
                doc.update_stream(xref, compressed_jpeg_bytes)

            except Exception:
                continue

    def compress(
        self,
        *,
        pdf_bytes: io.BytesIO,
        callback: Callable[..., Any] | None = None,
        quality: int = 75,
    ) -> io.BytesIO:
        try:
            pdf_bytes.seek(0)
            doc = pymupdf.open(stream=pdf_bytes.read(), filetype="pdf")
            total_pages = len(doc)

            if total_pages == 0:
                pdf_bytes.seek(0)
                return pdf_bytes

            # КРОК 1: Проходимо по сторінках і викликаємо наш новий метод

            for idx in range(total_pages):
                page = doc[idx]
                self._set_page_images_quality(page, doc=doc, quality=quality)

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

            # КРОК 2: Фінальне збереження у потік
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
                        "key": "convert.done",
                        "status": "info",
                    },
                )
            return compressed_stream

        except Exception as e:
            logger.error(f"Помилка під час стискання: {e}", exc_info=True)
            pdf_bytes.seek(0)
            return pdf_bytes
