import platform
import shutil
from pathlib import Path

class ConverterFactory:
   @staticmethod
   def _find_soffice_windows() -> str:
        """Суворий пошук LibreOffice на Windows."""
        # 1. Перевірка в системному PATH
        in_path = shutil.which("soffice")
        if in_path:
            return in_path
        
        # 2. Перевірка стандартних шляхів
        standard_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for p in standard_paths:
            if Path(p).exists():
                return p
        
        # 3. Якщо нічого не знайдено — викидаємо помилку, а не "сподіваємось"
        raise FileNotFoundError(
            "LibreOffice не знайдено в стандартних папках або PATH. "
            "Будь ласка, вкажіть шлях вручну через параметр 'soffice_path'."
        )

   @staticmethod
   def get_converter(chunk_size: int = 30, soffice_path: str = None):
        os_name = platform.system()

        if os_name == "Windows":
            try:
                from .ms_office_converter import MSOfficeConverter
                return MSOfficeConverter(chunk_size=chunk_size)
            except Exception as e:
                # Якщо MS Office немає, ми ПОВИННІ знайти LibreOffice або впасти з чіткою помилкою
                actual_soffice = soffice_path or ConverterFactory._find_soffice_windows()
                from .lib_office_converter import LibreOfficeConverter
                return LibreOfficeConverter(soffice_path=actual_soffice, chunk_size=chunk_size)
        
        else:
            # Для Linux/Mac аналогічно: або шлях, або shutil.which, або помилка
            actual_soffice = soffice_path or shutil.which("soffice")
            if not actual_soffice:
                raise FileNotFoundError("LibreOffice ('soffice') не знайдено в системі Linux/Mac.")
                
            from .lib_office_converter import LibreOfficeConverter
            return LibreOfficeConverter(soffice_path=actual_soffice, chunk_size=chunk_size)