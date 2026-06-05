import ctypes
import logging
import platform
import sys

import customtkinter as ctk
from tendo import singleton

from simple_to_pdf.app_gui.main_window import PDFMergerGUI
from simple_to_pdf.cli.logger import setup_logger
from simple_to_pdf.core import config
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.pdf import ConversionService, PageExtractor, PDFCompressor, PdfMerger
from simple_to_pdf.settings.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


def enable_dpi_awareness():
    """Налаштування коректного масштабування для Windows."""
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()


def main():
    """Initialize application components and launch the graphical user interface."""
    enable_dpi_awareness()
    try:
        me = singleton.SingleInstance(flavor_id="simple_to_pdf_unique_lock")  # noqa: F841
    except singleton.SingleInstanceException:
        sys.exit(0)
    settings_manager = SettingsManager(
        settings_path=config.SETTINGS_PATH, default_settings=config.DEFAULT_SETTINGS
    )
    LocalizationMixin.load_translations()
    setup_logger()
    merger = PdfMerger()
    page_extractor = PageExtractor()
    conversion_service = ConversionService()
    version_controller = VersionController(
        git_repo=config.GITHUB_REPO, git_user=config.GITHUB_USER
    )
    compressor = PDFCompressor()
    ctk.set_appearance_mode("light")
    _run_gui(
        conversion_service=conversion_service,
        merger=merger,
        page_extractor=page_extractor,
        version_controller=version_controller,
        settings_manager=settings_manager,
        compressor=compressor,
    )


def _run_gui(
    *,
    conversion_service: ConversionService,
    merger: PdfMerger,
    page_extractor: PageExtractor,
    version_controller: VersionController,
    settings_manager: SettingsManager,
    compressor: PDFCompressor,
) -> None:
    """Initialize and run the main application GUI loop."""
    try:
        app = PDFMergerGUI(
            conversion_service=conversion_service,
            merger=merger,
            page_extractor=page_extractor,
            version_controller=version_controller,
            settings_manager=settings_manager,
            compressor=compressor,
        )
        app.mainloop()
    except Exception as e:
        logger.fatal(f"GUI Runtime error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
