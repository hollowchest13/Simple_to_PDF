from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ConversionResult:
    success: list[tuple[int, bytes]] = field(default_factory=list)
    failed: list[tuple[int, Path]] = field(default_factory=list)


@dataclass
class ExtractionResult:
    successful: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)
    filename: str = ""
