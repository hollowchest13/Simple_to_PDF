from pypdf import PdfReader,PdfWriter
from pathlib import Path

class PdfMerger:
    def merge_pdfs(self ,*, pdfs:list[tuple[int,str]], output_path:str|Path) -> Path:
        writer=PdfWriter()
        for path_str in pdfs:
            path=Path(path_str)
            if path.exists() and path.suffix.lower() ==".pdf":
                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)
                print(f"✅ Added: {path}")
            else:
               print(f"⚠️ Warning: {path} does not exist or is not a .pdf file.") 
        
        output_file=Path(output_path)
        output_file.parent.mkdir(parents=True,exist_ok=True)
        
        with output_file.open("wb") as f:
            writer.write(f)
        
        print(f"📁 Merged PDF saved to: {output_file}")
        return output_file
