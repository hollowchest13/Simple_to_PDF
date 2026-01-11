from pypdf import PdfReader,PdfWriter
from pathlib import Path
import io
import logging
from src.simple_to_pdf.converters import get_converter

logger = logging.getLogger(__name__)

class PdfMerger:
    def __init__(self):
        self.converter = get_converter()

    def _get_pdfs_bytes(self, files: list[tuple[int, str]], callback = None) -> list[tuple[int, bytes]]:

        """Step 1: Convert files to PDF bytes."""

        total_inputs = len(files)
    
        # Massege to GUI, about starting (progress bar is at 0, but text has changed)

        if callback:
            start_status_message = f"Starting conversion of {total_inputs} files to PDF..."
            callback(
                stage = "Conversion", 
                progress_bar_mode = "indeterminate",
                current = 0, 
                total = total_inputs, 
                status_message = start_status_message
            )

        # Conversion process 
        converted_pdfs = self.converter.convert_to_pdf(files = files)
    
        total_converted = len(converted_pdfs)
        
        #  Update GUI after completion of the stage
        if callback:
            end_status_message = f"✅ Converted {total_converted} of {total_inputs} files."
            logger.info(end_status_message)
            callback(
            stage = "Conversion", 
            progress_bar_mode = "determinate",
            current = total_inputs, # Full progress
            total = total_inputs, 
            status_message = end_status_message
        )
        return converted_pdfs
    
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
