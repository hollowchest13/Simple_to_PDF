import logging

from simple_to_pdf.app_gui.app import PDFMergerGUI
from simple_to_pdf.cli.logger import setup_logger
from simple_to_pdf.pdf import PageExtractor, PdfMerger

logger = logging.getLogger(__name__)


def main():
    setup_logger()
    merger = PdfMerger()
    page_extractor = PageExtractor()

    run_gui(merger=merger, page_extractor=page_extractor)


def run_gui(*, merger: PdfMerger, page_extractor: PageExtractor) -> None:
    try:
        app = PDFMergerGUI(merger=merger, page_extractor=page_extractor)
        app.mainloop()
    except Exception as e:
        logger.fatal(f"❌ GUI Runtime error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
