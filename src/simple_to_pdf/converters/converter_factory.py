import logging
import platform
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class ConverterFactory:
    def __init__(self):
        self.chunk_size = 30

    def _find_soffice_windows(self) -> str:
        """Strict search for LibreOffice on Windows."""

        # 1. Check in system PATH
        in_path = shutil.which("soffice")
        if in_path:
            logger.info(f"LibreOffice found in PATH: {in_path}")
            return in_path

        # 2. Check standard paths
        standard_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
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

    def _get_libre_path(self, *, custom_path: str = None) -> str:
        """Find path to LibreOffice depending on the system"""

        if custom_path:
            return custom_path

        if platform.system() == "Windows":
            return self._find_soffice_windows()
        return shutil.which("soffice")

    def _try_ms_office(self, *, chunk_size: int):
        "Encapsulates import and creation of MSOfficeConverter"

        from simple_to_pdf.converters.ms_office_converter import MSOfficeConverter

        return MSOfficeConverter(chunk_size=chunk_size)

    def _try_libre_office(self, *, chunk_size: int):
        """Encapsulates import and creation of LibreOfficeConverter"""

        self.soffice_path = self._get_libre_path()

        if not self.soffice_path:
            raise FileNotFoundError("LibreOffice ('soffice') not found.")

        from simple_to_pdf.converters.lib_office_converter import (
            LibreOfficeConverter,
        )

        return LibreOfficeConverter(
            soffice_path=self.soffice_path, chunk_size=chunk_size
        )

    def _try_image_only(self, *, chunk_size: int):
        """Encapsulates import and creation of ImageConverter"""

        from simple_to_pdf.converters.img_converter import ImageConverter

        return ImageConverter(chunk_size=chunk_size)

    def get_converter(self):
        os_name = platform.system()
        logger.info(f"Operating System detected: {os_name}")
        strategies = []
        if os_name == "Windows":
            strategies = [
                lambda: self._try_ms_office(chunk_size=self.chunk_size),
                lambda: self._try_libre_office(chunk_size=self.chunk_size),
            ]
        elif os_name == "Linux":
            strategies = [lambda: self._try_libre_office(chunk_size=self.chunk_size)]
        strategies.append(lambda: self._try_image_only(chunk_size=self.chunk_size))
        for strategy in strategies:
            try:
                converter = strategy()
                logger.info(f"Using converter: {converter.__class__.__name__}")
                return converter
            except Exception as e:
                logger.warning(f"Converter initialization failed: {e}", exc_info=True)
