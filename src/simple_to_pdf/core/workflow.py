from simple_to_pdf.pdf import ConversionService, PageExtractor, PDFCompressor, PdfMerger


class WorkflowManager:
    def __init__(
        self,
        conversion_service: ConversionService | None = None,
        merger_service: PdfMerger | None = None,
        compressor_service: PDFCompressor | None = None,
        page_extractor: PageExtractor | None = None,
    ):
        self.conversion = conversion_service or ConversionService()
        self.merger = merger_service or PdfMerger()
        self.compressor = compressor_service or PDFCompressor()
        self.extractor = page_extractor or PageExtractor()

        # Управління процесами для швидкого скасування
        self._executor = None
