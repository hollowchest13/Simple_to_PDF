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
    
    def convert_images_to_pdf(self,*, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
       all_results = []
       for chunk in self.make_chunks(files, self.chunk_size):
            
            # Call the new method that handles one chunk
            all_results.extend(self._convert_images_chunk(chunk = chunk))
       return all_results

    def _convert_images_chunk(self,*, chunk: list[tuple[int,str]]) -> list[tuple[int, bytes]]:
        pdfs: list[tuple[int,bytes]] = []
        for idx,path_str in chunk:
            path = Path(path_str)
            if path.exists():
                try:
                    with Image.open(path).convert("RGB") as img:
                        rgb_img = img.convert("RGB")
                        buffer = io.BytesIO()
                        rgb_img.save(buffer, format="PDF")
                        pdfs.append((idx, buffer.getvalue()))
                except Exception as e:
                         logger.error(f"⚠️ [{idx}] Error: failed to convert image {path} ({e})", exc_info = True)
            else:
                logger.warning(f"⚠️ [{idx}] Skipped: {path} (not an image or missing)")
        return pdfs