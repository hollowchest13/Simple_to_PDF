import subprocess
import tempfile
import shutil
from pathlib import Path
from .base_converter import BaseConverter

class LibreOfficeConverter(BaseConverter):
   
   class LibreOfficeConverter(BaseConverter):
    def __init__(self, soffice_path: str, chunk_size: int = 30):
        # Call constructor of base class, so it can initialize its data
        super().__init__() 
        
        self.soffice_path = soffice_path
        self.chunk_size = chunk_size
    
   def convert_to_pdf(self,*, files: list[tuple[int, str]]) -> list[tuple[int, bytes]]:
        docs: list[tuple[int, Path]] = []
        imgs: list[tuple[int, Path]] = []
        pdfs: list[tuple[int, bytes]] = []
        converted: list[tuple[int, bytes]] = []

        for idx, path_str in files:
            path = Path(path_str)
            if path.exists():
                if self.is_pdf_file(file_path = path):
                     pdfs.append((idx,path.read_bytes()))
                elif self.is_excel_file(file_path = path) or self.is_word_file(file_path = path):
                    docs.append((idx,path))
                elif self.is_image_file(file_path = path):
                    imgs.append((idx,path))
                
        converted.extend(self._convert_docs_to_pdf(files = docs))
        converted.extend(self.convert_images_to_pdf(files = imgs))
        pdfs.extend(converted)
        return pdfs
   
   def _convert_docs_to_pdf(self,*, files: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
       all_results = []
       for chunk in self.make_chunks(files, self.chunk_size):
            # Call the new method that handles one chunk
            all_results.extend(self._convert_chunk(chunk))
       return all_results
   
   def _convert_chunk(self, chunk: list[tuple[int, Path]]) -> list[tuple[int, bytes]]:
        
        """Logic for processing one chunk of files."""
        
        results = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # 1. Prepare files (copy with index prefix)
            input_paths = self._prepare_temp_files(chunk, tmp_path)
            
            # 2. Run the conversion
            success = self._run_libreoffice_command(input_paths, tmp_path)
            
            # 3. if command was successful, collect results
            if success:
                results = self._collect_results(chunk, tmp_path)
                
        return results
   
   def _prepare_temp_files(self, chunk: list[tuple[int, Path]], tmp_path: Path) -> list[str]:
        
        """Copy files in temporary directory with index prefix."""

        paths = []
        for idx, original_path in chunk:
            temp_name = f"{idx}_{original_path.name}"
            temp_file_path = tmp_path / temp_name
            shutil.copy2(original_path, temp_file_path)
            paths.append(str(temp_file_path))
        return paths
   
   def _run_libreoffice_command(self, input_paths: list[str], out_dir: Path) -> bool:
        
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
            print(f"❌ LibreOffice error: {e}")
            return False
    
   def _collect_results(self, chunk: list[tuple[int, Path]], tmp_path: Path) -> list[tuple[int, bytes]]:
        
        """Reads created PDF files into memory."""

        chunk_results = []
        for idx, original_path in chunk:
            expected_pdf = tmp_path / f"{idx}_{original_path.stem}.pdf"
            if expected_pdf.exists():
                chunk_results.append((idx, expected_pdf.read_bytes()))
            else:
                print(f"⚠️ Файл не знайдено: {expected_pdf.name}")
        return chunk_results
   
   
   



    