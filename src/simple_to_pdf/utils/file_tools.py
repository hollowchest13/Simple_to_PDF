import logging
from tkinter import filedialog, messagebox
from typing import overload, Literal, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class FileToolKit:
    @staticmethod
    def write_bytes(*, file_path: Path, bytes_data: bytes) -> Path:
        """
        Safely writes bytes to a file.
        Automatically resolves the path and creates parent directories if needed.
        """
        clean_path = file_path.resolve()
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        clean_path.write_bytes(bytes_data)
        return clean_path

    @staticmethod
    def read_text_file(*, file_path: Path, encoding="utf-8") -> str:
        """Read and return text with right encoding"""
        if not file_path.exists():
            raise FileNotFoundError(f"File missing: {file_path}")

        raw_text = file_path.read_text(encoding=encoding)
        return raw_text


FileCategory = Literal["pdf", "table", "image", "document", "presentation"]


GLOBAL_EXTENSIONS: dict[FileCategory, set[str]] = {
    "pdf": {".pdf"},
    "table": {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".xlsb", ".ods", ".csv"},
    "document": {".doc", ".docx", ".odt", ".rtf", ".txt"},
    "presentation": {".ppt", ".pptx", ".odp"},
    "image": {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".gif",
        ".tiff",
        ".tif",
        ".webp",
        ".ppm",
        ".icns",
        ".ico",
        ".jfif",
        ".jpe",
        ".tga",
    },
}


def get_file_category(file_path: Path) -> FileCategory | None:
    """Return file category by path"""

    ext = file_path.suffix.lower()
    for category, exts in GLOBAL_EXTENSIONS.items():
        if ext in exts:
            return category
    return None


def get_text(*, file_name: str, file_path: str) -> str | None:
    path = Path(file_path)
    if not path.exists():
        messagebox.showwarning("Warning", f"{file_name} file not found")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        err_msg = f"Failed to read {file_name}: {e}"
        logger.error(err_msg, exc_info=True)
        messagebox.showerror("Error", err_msg)
        return


@overload
def get_files(
    *, filetypes: Union[list, tuple] = ..., multiple: Literal[True] = True
) -> tuple[str, ...]:
    """Returns a sequence of file paths when multiple=True."""
    ...


@overload
def get_files(*, filetypes: Union[list, tuple] = ..., multiple: Literal[False]) -> str:
    """Returns a single file path string when multiple=False."""
    ...


def get_files(
    *, filetypes: list | tuple = (".pdf",), multiple=True
) -> Union[tuple[str, ...], str]:
    """
    Open dialog window to select files.
    Supports both raw extensions: (".pdf", ".docx")
    and ready-made filters: [("Label", "*.ext"), ...]
    """

    if (
        isinstance(filetypes, list)
        and len(filetypes) > 0
        and isinstance(filetypes[0], tuple)
    ):
        filters = filetypes
    else:
        all_supported_mask = " ".join([f"*{ext}" for ext in filetypes])
        filters = [("All supported types", all_supported_mask)]

        for ext in filetypes:
            if isinstance(ext, str):
                filters.append((f"{ext.upper()} files", f"*{ext}"))
    if multiple:
        return filedialog.askopenfilenames(filetypes=filters)

    # For single selection, it's better to use dynamic filters instead of hardcoded PDF
    return filedialog.askopenfilename(filetypes=filters)
