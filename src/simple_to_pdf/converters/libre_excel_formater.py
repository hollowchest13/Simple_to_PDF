import logging 
from pathlib import Path
import openpyxl
from openpyxl.worksheet.properties import PageSetupProperties
logger = logging.getLogger(__name__)
class OpenPyXlFormatterMixin:
    """
    A mixin for formatting .xlsx files using the openpyxl library.
    Ideal for Linux environments as it modifies XML directly without requiring MS Excel.
    """

    def _prepare_excel_scaling(self, *, file_path: Path):
        """
        Configures Excel print and layout settings to ensure tables fit correctly 
        on the page and do not 'break' during conversion.
        """
        wb = None
        try:
            # Load the workbook. Using string representation of Path for compatibility.
            wb = openpyxl.load_workbook(str(file_path))

            for sheet in wb.worksheets:
                # 1. Orientation: Landscape for wide tables, Portrait for narrow ones.
                # Threshold set to 10 columns based on standard A4 width.
                if sheet.max_column > 10:
                    sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE
                else:
                    sheet.page_setup.orientation = sheet.ORIENTATION_PORTRAIT

                # 2. Scaling: Fit all columns to a single page width.
                # fitToHeight = 0 allows the height to scale automatically based on content.
                sheet.page_setup.fitToWidth = 1
                sheet.page_setup.fitToHeight = 0 

                # 3. Scaling Activation: fitToPage must be True for scaling properties to take effect.
                if sheet.sheet_properties.pageSetUpPr is None:
                    sheet.sheet_properties.pageSetUpPr = PageSetupProperties()
                
                sheet.sheet_properties.pageSetUpPr.fitToPage = True

                # 4. Paper Size: Standardize to A4 for consistent PDF rendering.
                sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
                
                # 5. Margins: Apply optimized narrow margins.
                self._apply_minimal_margins(sheet)

            # Save changes back to the file.
            wb.save(str(file_path))

        except Exception as e:
            # Note: Ensure a logger is configured in your main application context.
            logger.warning(f"⚠️ Failed to scale table file {file_path.name}: {e}")
        finally:
            if wb:
                wb.close()

    def _apply_minimal_margins(self, sheet):
        """
        Sets narrow margins (in inches) to maximize the usable printable area on the sheet.
        """
        sheet.page_margins.left = 0.15
        sheet.page_margins.right = 0.15
        sheet.page_margins.top = 0.2
        sheet.page_margins.bottom = 0.2