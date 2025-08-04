from pypdf import PdfReader, PdfWriter
from pathlib import Path
import os

class PdfManager:

    def __init__(self):
        self.pdf_list = []

    def add_pdf(self, pdf_path: str) -> None:
        pass

    def move_on_list(self, *, files: list[str],selected_idx:list[int], direction: str) -> list[str]:
        if not files or not selected_idx:
            return files
        result=files.copy()
        max_index = len(files) - 1
        if direction == "up":
            for idx in sorted(selected_idx):
                if idx > 0:
                    result[idx - 1], result[idx] = result[idx], result[idx - 1]
        elif direction == "down":
            for idx in sorted(selected_idx, reverse=True):
                if idx < max_index:
                    result[idx + 1], result[idx] = result[idx], result[idx + 1]
        return result

    def remove_from_list(self,*, selected: str,files:str) -> None:
        new_files_list= [item for item in files if item not in selected]
        return new_files_list

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
