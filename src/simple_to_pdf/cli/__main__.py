import logging

from simple_to_pdf.app_gui.app import run_gui
from simple_to_pdf.cli.logger import setup_logger

logger = logging.getLogger(__name__)


def main():
    setup_logger()
    run_gui()


if __name__ == "__main__":
    main()
