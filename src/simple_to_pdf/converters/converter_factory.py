import platform
import shutil
from pathlib import Path

class ConverterFactory:
   @staticmethod
   def _find_soffice_windows() -> str:
        
        """Strict search for LibreOffice on Windows."""
        
        # 1. Check in system PATH
        in_path = shutil.which("soffice")
        if in_path:
            return in_path

        # 2. Check standard paths
        standard_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for p in standard_paths:
            if Path(p).exists():
                return p

        # 3. If no LibreOffice found — raise an error
        raise FileNotFoundError(
            "LibreOffice not found in standard folders or PATH. "
            "Please specify the path manually via the 'soffice_path' parameter."
        )

   @staticmethod
   def get_converter(chunk_size: int = 30, soffice_path: str = None):
        os_name = platform.system()

        if os_name == "Windows":
            try:
                from .ms_office_converter import MSOfficeConverter
                return MSOfficeConverter(chunk_size=chunk_size)
            except Exception as e:
                # if MS Office not found, we MUST find LibreOffice or fail with a clear error
                actual_soffice = soffice_path or ConverterFactory._find_soffice_windows()
                from .lib_office_converter import LibreOfficeConverter
                return LibreOfficeConverter(soffice_path=actual_soffice, chunk_size=chunk_size)
        
        else:
            # For Linux/Mac similarly: either path, or shutil.which, or error
            actual_soffice = soffice_path or shutil.which("soffice")
            if not actual_soffice:
                raise FileNotFoundError("LibreOffice ('soffice') not found in Linux/Mac system.")
                
            from .lib_office_converter import LibreOfficeConverter
            return LibreOfficeConverter(soffice_path=actual_soffice, chunk_size=chunk_size)