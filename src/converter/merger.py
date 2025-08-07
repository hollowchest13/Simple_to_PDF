from pypdf import PdfReader, PdfWriter
from pathlib import Path
import os

class PdfManager:

    def __init__(self):
        self.pdf_list = []

    #Replace pdf on the list
    def move_on_list(self, *, files: list[str],selected_idx:list[int], direction: str) -> list[str]:
        
        # If no files or selected indexes, return the original list
        if not files or not selected_idx:
            return files
        result=files.copy()
        max_index = len(files) - 1

        # Sort selected indexes to handle multiple selections correctly
        if direction == "up":

            # Ensure we don't go out of bounds
            if any(idx==0 for idx in selected_idx):
                return files
            
            # Move selected items up in the list
            for idx in sorted(selected_idx):
                if idx > 0:
                    result[idx], result[idx - 1] = result[idx - 1], result[idx]
        elif direction == "down":

            # Ensure we don't go out of bounds
            if any(idx==max_index for idx in selected_idx):
                return files
            
            # Move selected items down in the list
            for idx in sorted(selected_idx, reverse=True):
                if idx < max_index:
                    result[idx], result[idx + 1] = result[idx + 1], result[idx]
        return result

    # Remove selected items from the list
    def remove_from_list(self,*, selected: str,files:str) -> None:
        new_files_list= [item for item in files if item not in selected]
        return new_files_list

    # Merge multiple PDFs into a single PDF file
    def merge_pdfs(self,*,pdfs: list[str], output_path: str) -> str:
        
        writer = PdfWriter()

        for path in pdfs:
            if os.path.exists(path) and path.lower().endswith('.pdf'):
                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)
                print(f"✅ Added: {path}")
            else:
                print(f"⚠️ Warning: {path} does not exist or is not a .pdf file.")

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"📁 Merged PDF saved to: {output_path}")
        return output_path
    
    # Remove pages from a PDF file
    def extract_pages(self, *, input_path: tuple[str], pages_to_extract: list[int], output_path: str) -> None:
        writer = PdfWriter()
        with open(input_path[0], "rb") as f:
            print(input_path[0])
            reader = PdfReader(f)
            total_pages = len(reader.pages)

            # Normalize page numbers to 0-based index and filter invalid entries

            if not pages_to_extract:
                raise ValueError("No valid pages to extract")

            # Add pages in the order specified, allowing duplicates
            for p in pages_to_extract:
                writer.add_page(reader.pages[p])

            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the new PDF file
        with open(output_path, "wb") as f:
            writer.write(f)

