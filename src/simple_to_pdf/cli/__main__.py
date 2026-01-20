from src.simple_to_pdf.app_gui.app import run_gui
from src.simple_to_pdf.cli.logger import setup_logger


def main():
    setup_logger()
    run_gui()


if __name__ == "__main__":
    main()
