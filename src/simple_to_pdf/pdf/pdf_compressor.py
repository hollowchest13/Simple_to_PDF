import logging
import io
from typing import Callable, Optional
logger=logging.getLogger(__name__)

class PDFCompressor:
    def __init__(self):
        pass

    def compress(self,*,pdf_bytes:io.BytesIO, callback:Optional[Callable[[int], None]] = None)->io.BytesIO:
        pass
