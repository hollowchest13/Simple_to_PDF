import logging
import sys
import traceback
import warnings

import customtkinter as ctk
from tendo import singleton

from simple_to_pdf.app_gui.main_window import PDFMergerGUI
from simple_to_pdf.cli.logger import setup_logger
from simple_to_pdf.core import config
from simple_to_pdf.core.version import VersionController
from simple_to_pdf.core.workflow import WorkflowManager
from simple_to_pdf.localization.localization_mixin import LocalizationMixin
from simple_to_pdf.pdf import ConversionService, PageExtractor, PDFCompressor, PdfMerger
from simple_to_pdf.settings.settings_manager import SettingsManager

warnings.filterwarnings("ignore", message="Annotation sizes differ")

logger = logging.getLogger(__name__)


def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    traceback.print_exception(exc_type, exc_value, exc_traceback)


def handle_tk_exception(exc_type, exc_value, exc_tb):
    logger.error("Tkinter exception", exc_info=(exc_type, exc_value, exc_tb))
    traceback.print_exception(exc_type, exc_value, exc_tb)


def main():
    """Initialize application components and launch the graphical user interface."""
    sys.excepthook = handle_exception
    ctk.CTk.report_callback_exception = handle_tk_exception
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
    workflow_manager = WorkflowManager(
        merger_service=merger,
        compressor_service=compressor,
        conversion_service=conversion_service,
        page_extractor_service=page_extractor,
    )
    ctk.set_appearance_mode("light")
    _run_gui(
        workflow_manager=workflow_manager,
        version_controller=version_controller,
        settings_manager=settings_manager,
    )


def _run_gui(
    *,
    workflow_manager: WorkflowManager,
    version_controller: VersionController,
    settings_manager: SettingsManager,
) -> None:
    """Initialize and run the main application GUI loop."""
    try:
        app = PDFMergerGUI(
            workflow_manager=workflow_manager,
            version_controller=version_controller,
            settings_manager=settings_manager,
        )
        app.mainloop()
    except Exception as e:  # noqa: BLE001
        logger.fatal(f"GUI Runtime error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
