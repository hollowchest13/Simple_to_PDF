from enum import IntEnum
from typing import Any
import logging

logger = logging.getLogger(__name__)

class XlSheetType(IntEnum):
    WORKSHEET = -4167
    CHART = 3

class Win32Orientation(IntEnum):
    PORTRAIT = 1
    LANDSCAPE = 2

class ExcelChartSize(IntEnum):
    SCREEN_SIZE = 1
    FULL_PAGE = 2
    SIZE_TO_FIT = 3
    
class MSExcelFormattingMixin():
    def _prepare_table_for_export(self,*,workbook:Any):
        
        """
        Setup printing options for a win32com Excel workbook.
        
        Args:
            workbook (Any): The Microsoft Excel Workbook object (win32com.client.CDispatch).
        """
        for sheet in workbook.Sheets:
            match sheet.type:
                case XlSheetType.WORKSHEET:

                    width = sheet.UsedRange.Columns.Count

                    # Page orientation setup
                    sheet.PageSetup.Orientation = 2 if width > 10 else 1

                    # Setup page scaling
                    sheet.PageSetup.Zoom = False
                    sheet.PageSetup.FitToPagesWide = 1
                    sheet.PageSetup.FitToPagesTall = 0
                case XlSheetType.CHART:
                    sheet.PageSetup.Orientation=2
                    try:
                        sheet.PageSetup.ChartSize=1
                    except Exception as e:
                        logger.error(f"❌ ChartSheet prepering error: {e}", exc_info=True)
                        pass
                case _:
                    pass
