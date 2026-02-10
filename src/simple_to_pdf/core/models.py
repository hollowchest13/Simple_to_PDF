from dataclasses import dataclass

@dataclass
class ReleaseInfo:
    version: str
    date: str
    notes: str