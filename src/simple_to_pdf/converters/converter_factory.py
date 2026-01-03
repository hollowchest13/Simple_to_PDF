import platform
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConverterFactory:
   @staticmethod
   def _find_soffice_windows() -> str:
        
        """Strict search for LibreOffice on Windows."""
        
        # 1. Check in system PATH
        in_path = shutil.which("soffice")
        if in_path:
            logger.info(f"LibreOffice found in PATH: {in_path}")
            return in_path

        # 2. Check standard paths
        standard_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for p in standard_paths:
            if Path(p).exists():
                logger.info(f"LibreOffice found at standard path: {p}")
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
                from src.simple_to_pdf.converters.ms_office_converter import MSOfficeConverter
                return MSOfficeConverter(chunk_size = chunk_size)
            except Exception as e:
                logger.warning(f"MS Office converter unavailable: {e}. Trying fallback to LibreOffice.")
                # if MS Office not found, we MUST find LibreOffice or fail with a clear error
                try:
                    actual_soffice = soffice_path or ConverterFactory._find_soffice_windows()
                    from src.simple_to_pdf.converters.lib_office_converter import LibreOfficeConverter
                    return LibreOfficeConverter(soffice_path = actual_soffice, chunk_size = chunk_size)
                except Exception as le:
                    logger.debug("All conversion engines failed on Windows.")
                    raise RuntimeError("Neither MS Office or LibreOffice converters are available.") from le
                    
        else:
            # For Linux similarly: either path, or shutil.which, or error
            actual_soffice = soffice_path or shutil.which("soffice")
            if not actual_soffice:
                logger.debug("LibreOffice ('soffice') conversion engine failed on Linux.")
                raise FileNotFoundError("LibreOffice ('soffice') not found in Linux system.")
            
            logger.info(f"Using LibreOffice on Linux: {actual_soffice}")    
            from src.simple_to_pdf.converters.lib_office_converter import LibreOfficeConverter
            return LibreOfficeConverter(soffice_path=actual_soffice, chunk_size = chunk_size)