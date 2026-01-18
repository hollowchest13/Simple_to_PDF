import subprocess
import tempfile
import shutil
import openpyxl
from pathlib import Path
from src.simple_to_pdf.converters.img_converter import ImageConverter

import logging

logger = logging.getLogger(__name__)

class LibreOfficeConverter(ImageConverter):

    SUPPORTED_FORMATS = {
        "table": {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".xlsb", ".ods", ".csv"},
        "document": {".doc", ".docx", ".odt", ".rtf", ".txt"},
        "presentation": {".ppt", ".pptx", ".odp"}
    }

    def __init__(self,*, soffice_path: str, chunk_size: int = 30):
        
        # Call constructor of base class, so it can initialize its data
        super().__init__() 
        
        self.soffice_path = soffice_path
        self.chunk_size = chunk_size
    
    def convert_to_pdf(self,*, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        docs: list[tuple[int, Path]] = []
        imgs: list[tuple[int, Path]] = []
        final_result: list[tuple[int, bytes]] = []

        for idx, path in files:
            if not path.exists():
                continue
            if self.is_table_file(file_path = path) or self.is_document_file(file_path = path) or self.is_presentation_file(file_path = path):
                docs.append((idx,path))
            elif self.is_image_file(file_path = path):
                imgs.append((idx,path))

        final_result.extend(self._convert_docs_to_pdf(files = docs))
        final_result.extend(self.convert_images_to_pdf(files = imgs))
        return final_result
   
    def _convert_docs_to_pdf(self,*, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
       all_results = []
       for chunk in self.make_chunks(files, self.chunk_size):
            
            # Call the new method that handles one chunk
            all_results.extend(self._convert_chunk(chunk = chunk))
       return all_results
    
    def _run_libreoffice_format_conversion(self,*, input_paths: list[Path], out_dir: Path):

        """all tables to xlsx conversion"""

        command = [
            self.soffice_path, '--headless', 
            '--convert-to', 'xlsx', 
            '--outdir', str(out_dir)
        ] + [str(p) for p in input_paths]
    
        try:
            subprocess.run(command, check = True, capture_output = True)
            # Deleting old xls
            for p in input_paths:
                if p.exists(): p.unlink()
        except Exception as e:
            logger.error(f"❌ Batch XLS conversion error: {e}")

    def _prepare_temp_files(self,*, chunk: list[tuple[int, Path]], tmp_path: Path) -> list[Path]:
        
        """Copy files in temporary directory with index prefix."""

        paths:Path = []
        for idx, original_path in chunk:
            temp_name = f"{idx}_{original_path.name}"
            temp_file_path = tmp_path / temp_name
            shutil.copy2(original_path, temp_file_path)
            paths.append(temp_file_path)
        return paths
   
    def _convert_chunk(self,*, chunk: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        
        """Logic for processing one chunk of files."""
        
        results = []
        to_convert_exts:list[str] = [".xls", ".xlsb", ".ods", ".csv"]
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Prepare files (copy with index prefix)
            all_tmp_paths:Path = self._prepare_temp_files(chunk = chunk, tmp_path = tmp_path)
           # Відбираємо ВСЕ, що потребує конвертації в .xlsx перед роботою openpyxl
            xls_to_convert: list[Path] = [
            p for p in all_tmp_paths 
            if p.suffix.lower() in to_convert_exts
            ]
            if xls_to_convert:
                self._run_libreoffice_format_conversion(input_paths = xls_to_convert, out_dir = tmp_path)
                all_tmp_paths = self._update_paths(all_paths = all_tmp_paths, to_check_exts = to_convert_exts)
            for path in all_tmp_paths:
                if path.suffix.lower() == ".xlsx":
                    self._prepare_excel_scaling(file_path = path)
            input_paths=[str(p) for p in all_tmp_paths]

            # Run the conversion
            success = self._run_libreoffice_command(input_paths = input_paths, out_dir = tmp_path)
            
            # if command was successful, collect results
            if success:
                results = self._collect_results(chunk = chunk, tmp_path = tmp_path)
                
        return results
    
    def _update_paths(self, *, all_paths: list[Path],to_check_exts:list[str]) -> list[Path]:
        updated = []
        for p in all_paths:
            if p.suffix.lower() in to_check_exts:
                expected = p.with_suffix(".xlsx")
                if expected.exists():
                    updated.append(expected)
                else:
                    logger.warning(f"⚠️ Conversion failed for {p.name}, keeping as {p.suffix}")
                    updated.append(p)
            else:
                # If it's .xlsx or any other file - just adding it back
                updated.append(p)
        return updated
    
    def _prepare_excel_scaling(self,*, file_path: Path):
        
        """
        Configures Excel print settings to prevent table 'breaking'.
        """
        try:
            wb = openpyxl.load_workbook(str(file_path))
        
            for sheet in wb.worksheets:
                # Detecting sheet orientation.
                max_col=sheet.max_column
                if max_col>10:
                    sheet.page_setup.orientation=sheet.ORIENTATION_LANDSCAPE
                else:
                    sheet.page_setup.orientation = sheet.ORIENTATION_PORTRAIT
            
                # Scaling: Fit all columns to one page width.
                sheet.page_setup.fitToWidth = 1
                sheet.page_setup.fitToHeight = 0
            
                # Enabling scaling mode (required for fitToWidth to take effect).
                sheet.sheet_properties.pageSetUpPr.fitToPage = True
            
                # Paper Size: Set to A4 (as a fallback/safety measure)
                sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
            
                # Margins: Set to minimum to maximize usable area
                sheet.page_margins.left = 0.15
                sheet.page_margins.right = 0.15
                sheet.page_margins.top = 0.2
                sheet.page_margins.bottom = 0.2
                wb.save(str(file_path))
        
        except Exception as e:
            logger.error(f"⚠️ Failed to scale Excel file {file_path.name}: {e}")
        finally:
            if wb:
                try:
                    wb.close()
                except:
                    pass
            
    def _run_libreoffice_command(self,*, input_paths: list[str], out_dir: Path) -> bool:
        
        """Run the LibreOffice conversion command."""

        command = [
            self.soffice_path, 
            '--headless', 
            '--convert-to', 'pdf',
            '--outdir', str(out_dir)
        ] + input_paths
        try:
            subprocess.run(command, check = True, capture_output = True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ LibreOffice error: {e}", exc_info = True)
            return False
    
    def _collect_results(self,*, chunk: list[tuple[int, Path]], tmp_path: Path) -> list[tuple[int, bytes]]:
        
        """Reads created PDF files into memory."""

        chunk_results = []
        for idx, original_path in chunk:
            expected_pdf = tmp_path / f"{idx}_{original_path.stem}.pdf"
            if expected_pdf.exists():
                chunk_results.append((idx, expected_pdf.read_bytes()))
            else:
                logger.warning(f"❌ File not found: {expected_pdf.name}")
        return chunk_results
    
    def get_excel_width(self,*, file_path: Path) -> dict[Path,int]:
        
        workbook = openpyxl.load_workbook(filename = file_path, data_only = True)
        report: dict[str,int] = {}
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            width = sheet.max_column if sheet.max_column else 0
            report[sheet_name] = width
        workbook.close
        return report