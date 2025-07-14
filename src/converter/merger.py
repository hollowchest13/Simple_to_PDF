from PyPDF2 import PdfMerger
import os
def merge_pdfs(pdf_list:list[str],output_path:str)->str:
    merger = PdfMerger()
    for path in pdf_list:
        if os.path.exists(path) and path.lower().endswith('.pdf'):
            merger.append(path)
        else:
            print(f"Warning: {path} does not exist and will be skipped.")
    merger.write(output_path)
    merger.close()
