import os
import logging
from tkinter import messagebox
from tkinter import filedialog

logger = logging.getLogger(__name__)

def get_text(*,file_name: str,file_path: str) -> str:
        if not os.path.exists(file_path):
            messagebox.showwarning("Warning", f"{file_name} file not found")
            return
        try:
            with open(file_path,"r",encoding = "utf-8") as f:
                return f.read()
        except Exception as e:
            err_msg=  f"Failed to read {file_name}: {e}"
            logger.error(err_msg,exc_info = True)
            messagebox.showerror("Error", err_msg)
            return

def get_files(*, filetypes: tuple[str, ...] = (".pdf",), multiple = True):

        """
        Open dialog window to select files.

        """
        # Create mask for all extensions together: "*.pdf *.docx *.xlsx"
        all_supported_mask = " ".join([f"*.{ext}" for ext in filetypes])
        
        # Form the list of filters
        # 1. First item — all supported types together
        filters = [("All supported types", all_supported_mask)]
        
        # 2. Then each type separately (for convenience)
        for ext in filetypes:
            filters.append((f"{ext.upper()} files", f"*.{ext}"))

        if multiple:
            return filedialog.askopenfilenames(filetypes = filters)
        return filedialog.askopenfilename(filetypes = [("PDF files", "*.pdf")])

def get_pages(*, raw: str) -> list[int] | None:
        pages: list[int] = []
        try:
            for part in raw.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.extend(range(start - 1, end))  # Convert to 0-based index
                else:
                    pages.append(int(part) - 1)  # Convert to 0-based index
            return pages
        except ValueError:
            return None
