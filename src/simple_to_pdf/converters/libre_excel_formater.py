import logging 
from pathlib import Path
import openpyxl
from openpyxl.worksheet.properties import PageSetupProperties
logger = logging.getLogger(__name__)

from enum import Enum, IntEnum

class ExcelPageConst(IntEnum):
    """General Excel page constants."""
    COL_THRESHOLD_LANDSCAPE = 10
    A4_PAPER_SIZE = 9  # Standard A4 in openpyxl/Excel

class ExcelMargins(Enum):
    """Standardized margins in inches."""
    SIDE = 0.15
    TOP_BOTTOM = 0.2

class OpenPyXlFormatterMixin:
    """Mixin for formatting .xlsx files using openpyxl with ChartSheet support."""

    def _prepare_excel_scaling(self, *, file_path: Path):
        """
        Configures print settings for all sheets including charts using Enum constants.
        """
        wb = None
        try:
            wb = openpyxl.load_workbook(str(file_path))

            # Process standard worksheets
            for sheet in wb.worksheets:
                self._setup_worksheet_scaling(sheet)
            
            # Process dedicated chart sheets if they exist
            if hasattr(wb, 'chartsheets'):
                for chart_sheet in wb.chartsheets:
                    self._setup_chartsheet_scaling(chart_sheet)

            wb.save(str(file_path))

        except Exception as e:
            logger.warning(f"⚠️ Failed to scale table file {file_path.name}: {e}")
        finally:
            if wb:
                wb.close()

    def _setup_worksheet_scaling(self, sheet):
        """Scaling logic specific to data worksheets (Worksheet object)."""
        # Determine orientation based on Enum threshold
        if sheet.max_column > ExcelPageConst.COL_THRESHOLD_LANDSCAPE:
            sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE
        else:
            sheet.page_setup.orientation = sheet.ORIENTATION_PORTRAIT

        # Activate Scaling mode
        if sheet.sheet_properties.pageSetUpPr is None:
            sheet.sheet_properties.pageSetUpPr = PageSetupProperties()
        sheet.sheet_properties.pageSetUpPr.fitToPage = True

        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0 
        
        self._apply_common_setup(sheet)

    def _setup_chartsheet_scaling(self, chart_sheet):
        """Scaling logic for dedicated chart sheets (Chartsheet object)."""
        # Charts are almost always better in Landscape for PDF
        chart_sheet.page_setup.orientation = chart_sheet.ORIENTATION_LANDSCAPE
        self._apply_common_setup(chart_sheet)

    def _apply_common_setup(self, sheet):
        """Applies margins and paper size from Enum constants."""
        sheet.page_setup.paperSize = ExcelPageConst.A4_PAPER_SIZE.value
        
        # Apply margins from Enum
        sheet.page_margins.left = ExcelMargins.SIDE.value
        sheet.page_margins.right = ExcelMargins.SIDE.value
        sheet.page_margins.top = ExcelMargins.TOP_BOTTOM.value
        sheet.page_margins.bottom = ExcelMargins.TOP_BOTTOM.value