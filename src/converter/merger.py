from pypdf import PdfReader, PdfWriter
import os

def merge_pdfs(pdf_list: list[str], output_path: str) -> str:
    writer = PdfWriter()

    for path in pdf_list:
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
