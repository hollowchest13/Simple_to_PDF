from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class ConversionResult:
    successful: list[tuple[int, bytes]] = field(default_factory=list)
    failed: list[tuple[int, Path]] = field(default_factory=list)
    
    @property
    def processed_ids(self) -> set[int]:
        """Returns a set of IDs that have already been processed (successfully or not)."""
        return {item[0] for item in self.successful} | {item[0] for item in self.failed}