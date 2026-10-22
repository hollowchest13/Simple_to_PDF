from dataclasses import dataclass
from enum import Enum


@dataclass
class ReleaseInfo:
    version: str
    date: str
    notes: str


@dataclass
class UpdateCheckResult:
    is_available: bool
    release: ReleaseInfo | None = None
    error_message: str | None = None


class App_Mode(Enum):
    COMPRESS = "compress"
    MERGE = "merge"
    CONVERT = "convert"
