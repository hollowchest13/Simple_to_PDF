from pathlib import Path
from PIL import Image
import io
import logging
from src.simple_to_pdf.converters.base_converter import BaseConverter


logger = logging.getLogger(__name__)

class ImageConverter(BaseConverter):

    SUPPORTED_FORMATS = {
        "image": {".jpg", ".jpeg", ".png"}
    }

    def __init__(self,*, chunk_size: int = 30):  
        super().__init__()
        self.chunk_size = chunk_size

    def convert_images_to_pdf(self,*, files: list[tuple[int,str]]) -> list[tuple[int, bytes]]:
        pdfs: list[tuple[int,bytes]] = []
        for idx,path_str in files:
            path=Path(path_str)
            if path.exists():
                try:
                    img = Image.open(path).convert("RGB")
                    buffer = io.BytesIO()
                    img.save(buffer,format = "PDF")
                    pdfs.append((idx,buffer.getvalue()))
                except Exception as e:
                         logger.error(f"⚠️ [{idx}] Error: failed to convert image {path} ({e})", exc_info = True)
            else:
                logger.warning(f"⚠️ [{idx}] Skipped: {path} (not an image or missing)")
        return pdfs