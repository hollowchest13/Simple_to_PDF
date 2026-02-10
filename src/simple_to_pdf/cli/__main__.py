import logging

from simple_to_pdf.app_gui.app import PDFMergerGUI
from simple_to_pdf.cli.logger import setup_logger
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.pdf import PageExtractor, PdfMerger

logger = logging.getLogger(__name__)

GITHUB_USER = "hollowchest13"
GITHUB_REPO = "Simple_to_PDF"

# Dynamically constructing URLs for easier modification.
GITHUB_REPO_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"

# Path to the version.json file in the cli directory

README_URL = f"{GITHUB_REPO_URL}#readme"
RELEASES_URL = f"{GITHUB_REPO_URL}/releases"


def main():
    setup_logger()
    merger = PdfMerger()
    page_extractor = PageExtractor()
    version_controler = VersionController(git_repo=GITHUB_REPO, git_user=GITHUB_USER)

    run_gui(merger=merger, page_extractor=page_extractor)


def run_gui(*, merger: PdfMerger, page_extractor: PageExtractor) -> None:
    try:
        app = PDFMergerGUI(merger=merger, page_extractor=page_extractor)
        app.mainloop()
    except Exception as e:
        logger.fatal(f"❌ GUI Runtime error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
