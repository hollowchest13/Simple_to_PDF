from pypdf import PdfReader,PdfWriter
from pathlib import Path
import io
import logging
from src.simple_to_pdf.converters import ConverterFactory

logger = logging.getLogger(__name__)

class PdfMerger:
    def __init__(self):
        factory = ConverterFactory()
        self.converter = factory.get_converter()


    def _get_pdfs_bytes(self, files: list[tuple[int, str]], callback = None) -> list[tuple[int, bytes]]:

        """Step 1: Convert files to PDF bytes."""

        # total_inputs = len(files)

        # Massege to GUI, about starting (progress bar is at 0, but text has changed)
        # stage = "Processing"
        pdf_bytes:list[tuple[int,bytes]] = []
        to_conversion:list[tuple[int,Path]] = []
        total_inputs: int = len(files)

        for idx, path_str in files:
            path = Path(path_str)
            if not path.exists():
                continue
            if self.converter.is_pdf_file(file_path = path):
                pdf_bytes.append((idx, path.read_bytes()))
            elif self.converter.needs_conversion(file_path = path):
                to_conversion.append((idx,path))
        total_to_conversion: int = len(to_conversion)

        if not total_to_conversion:
            return pdf_bytes
        stage:str = "Conversion"
        if callback:
           
            start_status_message = f"Starting conversion of {total_to_conversion} files to PDF..."
            callback(
                stage = stage, 
                progress_bar_mode = "indeterminate",
                current = 0, 
                total=total_inputs, 
                status_message = start_status_message
            )
        converted: list[tuple[int,bytes]] = self.converter.convert_to_pdf(files = to_conversion)
        total_converted: int = len(converted)
        if callback:
            start_status_message = f"✅ Converted {total_converted} of {total_to_conversion} files."
            callback(
                stage = stage, 
                progress_bar_mode = "determinate",
                current = 100, 
                total = total_inputs, 
                status_message = start_status_message
            )
        pdf_bytes.extend(converted)
        pdf_bytes.sort(key = lambda x: x[0])
        return pdf_bytes

        
    def merge_to_pdf(self, *, files: list[tuple[int, str]], output_path: str | Path, callback = None) -> Path:

        """Merges multiple files into a single PDF."""

        files_sorted = sorted(files, key = lambda x: x[0])
        names_lookup = {file_idx: file_name for file_idx, file_name in files_sorted}

        # 1. Convertation
        pdfs_sorted: list[tuple[int, bytes]] = self._get_pdfs_bytes(files = files, callback = callback)

        writer = PdfWriter()
        total = len(pdfs_sorted)

        # 2. Base cycle of merging
        for i, (idx, pdf_bytes) in enumerate(pdfs_sorted, 1):
            try:
                reader = PdfReader(io.BytesIO(pdf_bytes))
                current_filename = Path(names_lookup.get(idx, f"File {idx}")).name
                for page in reader.pages:
                    writer.add_page(page)

                # If GUI gives us a function to update progress, we call it
                if callback:
                    # We pass current, total and filename
                    # (Since there's no filename here, we can just use index or "File X")
                    callback(stage = "Merging", progress_bar_mode = "determinate", current = i, total = total, filename = f"Document {current_filename}")
            except Exception as e:
                logger.error(f"⚠️ Failed to read PDF with name {current_filename}: ({e})", exc_info = True)
                
        if len(writer.pages) == 0:
            raise RuntimeError("Failed to add any pages. Input files are corrupted or empty.")
        
        # 3. Saving the result
        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents = True, exist_ok = True)

        with output_file.open("wb") as f:
            writer.write(f)
        return output_file
