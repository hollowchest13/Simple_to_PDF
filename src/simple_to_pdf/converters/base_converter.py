from pathlib import Path

import logging

logger = logging.getLogger(__name__)

class BaseConverter():

    SUPPORTED_FORMATS = {
        "pdf": {".pdf"}
        }

    def __init__(self,*, chunk_size: int = 30):
        self.chunk_size = chunk_size

    @staticmethod
    def make_chunks(lst, n):

        """Splits list lst into chunks of n elements."""

        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    @classmethod
    def get_supported_formats(cls) -> dict:
        """
        Gets dictionaries from all inheritance chain.
        Method lies in Base, but knows about descendants' formats via cls.
        """
        combined = {}
        # reversed(cls.__mro__) іде від object -> BaseConverter -> Нащадок
        for base in reversed(cls.__mro__):
            # getattr(base, ...) finds SUPPORTED_FORMATS in each class
            formats = getattr(base, 'SUPPORTED_FORMATS', {})
            # .update() replaces old values with new ones or adds new keys
            combined.update(formats)
        return combined
    
    def _check_extension(self,*, file_path: Path, category: str) -> bool:

        """Check Extensions."""

        # 1. Get FULL dictionary of formats (with all descendants)
        all_formats = self.get_supported_formats()
        
        # 2. Use .get() to avoid KeyError if category doesn't exist
        allowed_exts = all_formats.get(category, set())
        return file_path.suffix.lower() in allowed_exts
    
    def is_pdf_file(self,*, file_path: Path) -> bool:
        return self._check_extension(file_path = file_path, category = "pdf")

    def is_table_file(self,*, file_path: Path) -> bool:
         return self._check_extension(file_path = file_path, category = "table")
           
    def is_image_file(self,*, file_path: Path) -> bool:
        return self._check_extension(file_path = file_path, category = "image")
    
    def is_document_file(self,*, file_path: Path) -> bool:
        return self._check_extension(file_path = file_path, category = "document")
    
    def is_presentation_file(self,*, file_path: Path) -> bool:
        return self._check_extension(file_path = file_path, category = "presentation")

    def needs_conversion(self,*,file_path: Path) -> bool:

        """ Checks if the file extension is in SUPPORTED_FORMATS (excluding PDF)."""

        # Create a flat set of all extensions that need conversion
        # We skip 'pdf' during this process
        convertible_exts = {
            ext 
            for category, exts in self.SUPPORTED_FORMATS.items() 
            if category != "pdf" 
            for ext in exts
        }
        # Get the extension of the input file and check
        file_ext = file_path.suffix.lower()
        return file_ext in convertible_exts
