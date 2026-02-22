import openpyxl
import logging
from pathlib import Path
from enum import Enum,IntEnum

logger = logging.getLogger(__name__)

class TableScaling(IntEnum):
    SINGLE_PAGE = 1
    UNLIMITED = 0

class ExcelMargins(Enum):
    LEFT_RIGHT_MARGIN = 0.15
    TOP_BOTTOM_MARGIN = 0.2

class LibreSetupMixin():
    def _prepare_excel_scaling(self, *, file_path: Path):
        """
        Configures Excel print settings to prevent table 'breaking'.
        """
        wb = None
        MAX_COL_WIDTH=10
        try:
            wb = openpyxl.load_workbook(str(file_path))

            for sheet in wb.worksheets:
                # Detecting sheet orientation.
                max_col = sheet.max_column
                if max_col > MAX_COL_WIDTH:
                    sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE
                else:
                    sheet.page_setup.orientation = sheet.ORIENTATION_PORTRAIT

                # Scaling: Fit all columns to one page width.
                sheet.page_setup.fitToWidth = TableScaling.SINGLE_PAGE.value
                sheet.page_setup.fitToHeight = TableScaling.UNLIMITED.value

                # Enabling scaling mode (required for fitToWidth to take effect).
                assert sheet.sheet_properties.pageSetUpPr is not None
                sheet.sheet_properties.pageSetUpPr.fitToPage = True

                # Paper Size: Set to A4 (as a fallback/safety measure)
                sheet.page_setup.paperSize = sheet.PAPERSIZE_A4

                # Margins: Set to minimum to maximize usable area
                sheet.page_margins.left = ExcelMargins.LEFT_RIGHT_MARGIN.value
                sheet.page_margins.right = ExcelMargins.LEFT_RIGHT_MARGIN.value
                sheet.page_margins.top = ExcelMargins.TOP_BOTTOM_MARGIN.value
                sheet.page_margins.bottom = ExcelMargins.TOP_BOTTOM_MARGIN.value
        except Exception as e:
            logger.error(f"⚠️ Failed to scale table file {file_path.name}: {e}")
        finally:
            if wb is not None:
                try:
                    wb.save(str(file_path))
                    wb.close()
                except Exception as e:
                    logger.error(f"⚠️ Failed to save table file {file_path.name}: {e}")