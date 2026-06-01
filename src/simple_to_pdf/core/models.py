from dataclasses import dataclass
from typing import Optional
from enum import Enum


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


class App_Mode(Enum):
    COMPRESS = "compress"
    MERGE = "merge"
    CONVERT = "convert"
