import logging

from simple_to_pdf.app_gui.main_window import PDFMergerGUI
from simple_to_pdf.cli.logger import setup_logger
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.pdf import PageExtractor, PdfMerger
from simple_to_pdf.core import config

logger = logging.getLogger(__name__)

def main():
    setup_logger()
    merger = PdfMerger()
    page_extractor = PageExtractor()
    version_controller = VersionController(git_repo=config.GITHUB_REPO, git_user=config.GITHUB_USER)

    run_gui(merger=merger, page_extractor=page_extractor,version_controller=version_controller)


def run_gui(*, merger: PdfMerger, page_extractor: PageExtractor,version_controller:VersionController) -> None:
    try:
        app = PDFMergerGUI(merger=merger, page_extractor=page_extractor,version_controller=version_controller)
        app.mainloop()
    except Exception as e:
        logger.fatal(f"❌ GUI Runtime error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
