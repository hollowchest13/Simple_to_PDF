from dataclasses import dataclass
from typing import Optional

@dataclass
class ReleaseInfo:
    version: str
    date: str
    notes: str

@dataclass
class UpdateCheckResult:
    is_available: bool
    release: Optional[ReleaseInfo] = None
    error_message: Optional[str] = None