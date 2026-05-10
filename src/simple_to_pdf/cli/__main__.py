import logging
import sys
import customtkinter as ctk
from simple_to_pdf.app_gui.main_window import PDFMergerGUI
from simple_to_pdf.cli.logger import setup_logger
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.pdf import PageExtractor, PdfMerger
from simple_to_pdf.core import config
from simple_to_pdf.settings.settings_manager import SettingsManager
from tendo import singleton
from simple_to_pdf.localization.localization_mixin import LocalizationMixin


logger = logging.getLogger(__name__)


def main():
    try:
        me = singleton.SingleInstance(flavor_id="simple_to_pdf_unique_lock")
    except singleton.SingleInstanceException:
        sys.exit(0)
    settings_manager = SettingsManager(
        settings_path=config.SETTINGS_PATH, default_settings=config.DEFAULT_SETTINGS
    )
    LocalizationMixin.load_translations()
    setup_logger()
    merger = PdfMerger()
    page_extractor = PageExtractor()
    version_controller = VersionController(
        git_repo=config.GITHUB_REPO, git_user=config.GITHUB_USER
    )
    ctk.set_appearance_mode("light")
    _run_gui(
        merger=merger,
        page_extractor=page_extractor,
        version_controller=version_controller,
        settings_manager=settings_manager,
    )


def _run_gui(
    *,
    merger: PdfMerger,
    page_extractor: PageExtractor,
    version_controller: VersionController,
    settings_manager: SettingsManager,
) -> None:
    try:
        app = PDFMergerGUI(
            merger=merger,
            page_extractor=page_extractor,
            version_controller=version_controller,
            settings_manager=settings_manager,
        )
        app.mainloop()
    except Exception as e:
        logger.fatal(f"❌ GUI Runtime error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
