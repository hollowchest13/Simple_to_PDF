import logging
import shutil
from abc import abstractmethod
from pathlib import Path

from simple_to_pdf.base_services.base import BaseService
from simple_to_pdf.converters.models import ConversionResult
from simple_to_pdf.utils.file_tools import get_unique_path

logger = logging.getLogger(__name__)


class BaseConverter(BaseService):
    SUPPORTED_FORMATS = {"pdf": {".pdf"}}  # noqa: RUF012

    def __init__(self, *, chunk_size: int = 30):
        super().__init__()
        self.chunk_size = chunk_size

    @abstractmethod
    def convert_to_pdf(
        self, *, files: list[tuple[int, Path]], out_dir: Path
    ) -> ConversionResult:
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

    def _prepare_temp_files(
        self, *, chunk: list[tuple[int, Path]], tmp_dir: Path
    ) -> list[Path]:
        """Copy files in temporary directory with index prefix."""

        paths: list[Path] = []
        for idx, original_path in chunk:
            temp_name = f"{idx}_{original_path.name}"
            temp_file_path = tmp_dir / temp_name
            temp_file_path = get_unique_path(temp_file_path)
            shutil.copy2(original_path, temp_file_path)
            paths.append(temp_file_path)
        return paths
