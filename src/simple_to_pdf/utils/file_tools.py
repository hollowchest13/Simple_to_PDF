import logging
import os
from tkinter import filedialog, messagebox
from typing import overload, Literal, Sequence, Union

logger = logging.getLogger(__name__)


def get_text(*, file_name: str, file_path: str) -> str|None:
    if not os.path.exists(file_path):
        messagebox.showwarning("Warning", f"{file_name} file not found")
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        err_msg = f"Failed to read {file_name}: {e}"
        logger.error(err_msg, exc_info=True)
        messagebox.showerror("Error", err_msg)
        return

@overload
def get_files(*, filetypes: Union[list, tuple] = ..., multiple: Literal[True] = True) ->tuple[str, ...]: 
    """Returns a sequence of file paths when multiple=True."""
    ...

@overload
def get_files(*, filetypes: Union[list, tuple] = ..., multiple: Literal[False]) -> str: 
    """Returns a single file path string when multiple=False."""
    ...

def get_files(*, filetypes: list | tuple = (".pdf",), multiple=True)-> Union[tuple[str, ...], str]:
    """
    Open dialog window to select files.
    Supports both raw extensions: (".pdf", ".docx")
    and ready-made filters: [("Label", "*.ext"), ...]
    """

    # Check if filetypes is already in (label, pattern) format
    if (
        isinstance(filetypes, list)
        and len(filetypes) > 0
        and isinstance(filetypes[0], tuple)
    ):
        filters = filetypes
    else:
        # Logic for raw extensions
        all_supported_mask = " ".join([f"*{ext}" for ext in filetypes])
        filters = [("All supported types", all_supported_mask)]

        for ext in filetypes:
            if isinstance(ext, str):
                filters.append((f"{ext.upper()} files", f"*{ext}"))
    if multiple:
        return filedialog.askopenfilenames(filetypes=filters)

    # For single selection, it's better to use dynamic filters instead of hardcoded PDF
    return filedialog.askopenfilename(filetypes=filters)
