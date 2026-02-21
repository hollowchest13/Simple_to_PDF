from typing import Any
import logging

logger = logging.getLogger(__name__)

from enum import IntEnum, Enum

class ExcelMargins(Enum):
    """Standardized margins in inches."""
    SIDE = 0.15
    TOP_BOTTOM = 0.2

class XlSheetType(IntEnum):
    """Excel sheet types for win32com API."""
    WORKSHEET = -4167
    CHART = 3

class Win32Orientation(IntEnum):
    """Orientation constants for win32com API."""
    PORTRAIT = 1
    LANDSCAPE = 2

class ExcelChartSize(IntEnum):
    """
    Constants for ChartSheet scaling in win32com.
    1: SCREEN_SIZE - fits the chart to the window size.
    2: FULL_PAGE - fits the chart to the entire printed page.
    3: SIZE_TO_FIT - resizes the chart to fit within the page margins.
    """
    SCREEN_SIZE = 1
    FULL_PAGE = 2
    SIZE_TO_FIT = 3
    
class ExcelPageConst(IntEnum):
    """General Excel page constants."""
    COL_THRESHOLD_LANDSCAPE = 10
    A4_PAPER_SIZE = 9
    FIT_TO_ONE_PAGE = 1
    AUTOMATIC_SCALING = 0  # Maps to False/0 in win32com for 'Auto' height/width

class MSExcelFormattingMixin:
    def _prepare_table_for_export(self, *, workbook: Any):
        """
        Setup printing options for a win32com Excel workbook.
        """
        for sheet in workbook.Sheets:
            # Using Enum for sheet type detection
            match sheet.type:
                case XlSheetType.WORKSHEET:
                    width = sheet.UsedRange.Columns.Count
                    
                    # Page orientation setup using Enum
                    sheet.PageSetup.Orientation = (
                        Win32Orientation.LANDSCAPE if width > ExcelPageConst.COL_THRESHOLD_LANDSCAPE 
                        else Win32Orientation.PORTRAIT
                    )

                    # Setup page scaling
                    sheet.PageSetup.Zoom = False
                    sheet.PageSetup.FitToPagesWide = ExcelPageConst.FIT_TO_ONE_PAGE
                    sheet.PageSetup.FitToPagesTall = ExcelPageConst.AUTOMATIC_SCALING # 0 in win32 means 'Automatic'
                
                case XlSheetType.CHART:
                    sheet.PageSetup.Orientation = Win32Orientation.LANDSCAPE
                    try:
                        # Use Enum for ChartSize if needed
                        sheet.PageSetup.ChartSize = ExcelChartSize.SCREEN_SIZE
                    except Exception as e:
                        logger.error(f"❌ ChartSheet preparation error: {e}", exc_info=True)