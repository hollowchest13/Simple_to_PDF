import logging

import tomllib

from simple_to_pdf.core.config import get_project_config_path

logger = logging.getLogger(__name__)


class VersionController:
    def __init__(self):
        self.local_version = self._get_local_version()

    def _get_local_version() -> str:
        default_version = "0.0.0"
        try:
            config_toml_path = get_project_config_path()
            with open(config_toml_path, "rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", default_version)
        except FileNotFoundError:
            logger.error("Error", f"File {config_toml_path} not found")
        except PermissionError:
            logger.error("Error", f"Permission denied to {config_toml_path}")
        except Exception as e:
            logger.error(
                f"Unexpected path error: {type(e).__name__} - {e}", exc_info=True
            )
        return default_version
