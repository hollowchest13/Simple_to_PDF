from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
import io
class BaseConverter(ABC):
    
    @abstractmethod
    def convert_excel_to_pdf(self,*, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        """Абстрактний метод, який мають реалізувати всі класи"""
        pass

    @abstractmethod
    def convert_word_to_pdf(self, *, word_files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        """Абстрактний метод, який мають реалізувати всі класи"""
        pass

    def convert_images_to_pdf(self,*, files: list[tuple[int,str]])->list[tuple[int, bytes]]:
        pdfs: list[tuple[int,bytes]] = []
        for idx,path_str in files:
            path=Path(path_str)
            if path.exists():
                try:
                    img=Image.open(path).convert("RGB")
                    buffer=io.BytesIO()
                    img.save(buffer,format="PDF")
                    pdfs.append((idx,buffer.getvalue()))
                except Exception as e:
                     print(f"⚠️ [{idx}] Warning: failed to convert image {path} ({e})")
                else:
                    print(f"⚠️ [{idx}] Skipped: {path} (not an image or missing)")
        return pdfs