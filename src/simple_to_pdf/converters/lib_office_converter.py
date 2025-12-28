from pathlib import Path
from .base_converter import BaseConverter

class LibreOfficeConverter(BaseConverter):
    
    # 1. Реалізація для Excel (аргумент ОБОВ'ЯЗКОВО 'files')
    def convert_excel_to_pdf(self, *, excel_files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        print("LibreOffice: Excel converter triggered")
        return []

    # 2. Реалізація для Word (аргумент ОБОВ'ЯЗКОВО 'word_files')
    def convert_word_to_pdf(self, *, word_files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        print("LibreOffice: Word converter triggered")
        return []

    # 3. Додатковий загальний метод (якщо він вам потрібен для логіки)
    def convert_to_pdf(self, input_paths, output_path):
        pass