from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple


class PageFormat(NamedTuple):
    width: float
    height: float

    @property
    def size(self) -> tuple[float, float]:
        return (self.width, self.height)


@dataclass
class PixInfo:
    width: int
    height: int
    samples: bytes


@dataclass
class BytePdfDocument:
    index: int
    data: bytes
    original_path: Path


@dataclass
class ProcessingReport:
    documents: list[BytePdfDocument] = field(default_factory=list)
    success: int = 0
    failed: int = 0
