import sys
from pathlib import Path


def get_project_config_path(self) -> Path:
    config_file_name: str = "pyproject.toml"
    if getattr(sys, "frozen", False):
        base_path: Path = Path(sys.executable).parent
    else:
        base_path: Path = Path(__file__).resolve().parent.parent.parent
    config_path = base_path / config_file_name
    return config_path
