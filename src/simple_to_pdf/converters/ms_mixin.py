import logging
from enum import IntEnum
logger = logging.getLogger(__name__)

class ExcelScaling(IntEnum):
    """
    Special values for FitToPages. 
    Note: For FitToPagesTall/Wide, False (or 0) means 'unlimited'.
    """
    SINGLE_PAGE = 1
    UNLIMITED = 0

class ExcelOrientation(IntEnum):
    """XlPageOrientation enumeration"""
    PORTRAIT = 1    # xlPortrait
    LANDSCAPE = 2   # xlLandscape

class MSSetupMixin():
    def _prepare_table_for_export(self, wb):
        """Setup printing options"""

        for sheet in wb.Sheets:
            try:
                
                if hasattr(sheet, "UsedRange"):
                    sheet.PageSetup.Zoom = False
                    width = sheet.UsedRange.Columns.Count
                    
                    # Page orientation setup
                    sheet.PageSetup.Orientation = ExcelOrientation.LANDSCAPE if width > 10 else ExcelOrientation.PORTRAIT
                    sheet.PageSetup.FitToPagesWide = ExcelScaling.SINGLE_PAGE
                    sheet.PageSetup.FitToPagesTall = False
                else:
                    sheet.PageSetup.Orientation = ExcelOrientation.LANDSCAPE
                    sheet.PageSetup.FitToPagesWide = ExcelScaling.SINGLE_PAGE
                    sheet.PageSetup.FitToPagesTall = ExcelScaling.SINGLE_PAGE
            except Exception as e:
                logger.warning(f"⚠️ Cannot setup PageSetup for {sheet.Name}: {e}")