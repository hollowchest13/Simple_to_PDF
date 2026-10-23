from collections.abc import Iterable
from pathlib import Path


def expand_paths(items: Iterable[str]) -> list[Path]:
    """Files as is, folders expanded into their direct files."""
    files: list[Path] = []
    for item in items:
        path = Path(item)
        if path.is_dir():
            files.extend(p for p in path.iterdir() if p.is_file())
        elif path.is_file():
            files.append(path)
    return files


def split_supported(
    files: list[Path], supported_exts: set[str]
) -> tuple[list[Path], int]:
    supported = [p for p in files if p.suffix.lower() in supported_exts]
    return supported, len(files) - len(supported)


def filter_new(files: list[Path], existing: Iterable[str | Path]) -> list[Path]:
    """Drop files already in the list and duplicates within the batch."""
    seen = {Path(p).resolve() for p in existing}
    new_files: list[Path] = []
    for p in files:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        new_files.append(p)
    return new_files


def format_extensions(exts: Iterable[str]) -> str:
    items = sorted({f".{e.lower().lstrip('.')}" for e in exts if e})
    return ", ".join(items)
