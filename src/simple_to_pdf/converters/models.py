from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConversionResult:
    success: list[tuple[int, Path]] = field(default_factory=list)
    failed: list[tuple[int, Path]] = field(default_factory=list)


@dataclass
class ExtractionResult:
    successful: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)
    filename: str = ""
