from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class PageFormat(Enum):
    A4 = (595.0, 842.0)
    A3 = (842.0, 1191.0)
    A5 = (420.0, 595.0)
    LETTER = (612.0, 792.0)
    LEGAL = (612.0, 1008.0)

    @property
    def width(self) -> float:
        return self.value[0]

    @property
    def height(self) -> float:
        return self.value[1]

    @property
    def size(self) -> tuple[float, float]:
        return self.value


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
