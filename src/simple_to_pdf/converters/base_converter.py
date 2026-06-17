import logging
from pathlib import Path
from abc import abstractmethod
from simple_to_pdf.base_services.base import BaseService
from simple_to_pdf.converters.models import ConversionResult

logger = logging.getLogger(__name__)


class BaseConverter(BaseService):
    SUPPORTED_FORMATS = {"pdf": {".pdf"}}

    def __init__(self, *, chunk_size: int = 30):
        self.chunk_size = chunk_size

    @abstractmethod
    def convert_to_pdf(self, *, files: list[tuple[int, Path]]) -> ConversionResult:
        pass

    @staticmethod
    def make_chunks(lst, n):
        """Splits list lst into chunks of n elements."""

        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    @classmethod
    def get_supported_formats(cls) -> dict:
        """
        Gets dictionaries from all inheritance chain.
        Method lies in Base, but knows about descendants' formats via cls.
        """
        combined = {}
        for base in reversed(cls.__mro__):
            formats = getattr(base, "SUPPORTED_FORMATS", {})
            combined.update(formats)
        return combined

    def _check_extension(self, *, file_path: Path, category: str) -> bool:
        """Check Extensions."""

        all_formats = self.get_supported_formats()

        allowed_exts = all_formats.get(category, set())
        return file_path.suffix.lower() in allowed_exts

    def is_pdf_file(self, *, file_path: Path) -> bool:
        return self._check_extension(file_path=file_path, category="pdf")

    def is_table_file(self, *, file_path: Path) -> bool:
        return self._check_extension(file_path=file_path, category="table")

    def is_image_file(self, *, file_path: Path) -> bool:
        return self._check_extension(file_path=file_path, category="image")

    def is_document_file(self, *, file_path: Path) -> bool:
        return self._check_extension(file_path=file_path, category="document")

    def is_presentation_file(self, *, file_path: Path) -> bool:
        return self._check_extension(file_path=file_path, category="presentation")

    def needs_conversion(self, *, file_path: Path) -> bool:
        """Checks if the file extension is in SUPPORTED_FORMATS (excluding PDF)."""

        convertible_exts = {
            ext
            for category, exts in self.SUPPORTED_FORMATS.items()
            if category != "pdf"
            for ext in exts
        }
        file_ext = file_path.suffix.lower()
        return file_ext in convertible_exts
