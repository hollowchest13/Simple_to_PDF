import logging

import requests
import tomllib
from packaging import version
from simple_to_pdf.core import config
from simple_to_pdf.core.models import ReleaseInfo, UpdateCheckResult
from simple_to_pdf.utils.network import fetch_remote_content

logger = logging.getLogger(__name__)


class VersionController:
    def __init__(self, *, git_repo: str, git_user: str):
        self._git_repo: str = git_repo
        self._git_user: str = git_user

    def _get_version_toml_url(self) -> str:
        version_toml_url = f"https://raw.githubusercontent.com/{self._git_user}/{self._git_repo}/main/pyproject.toml"
        return version_toml_url

    def _get_release_url(self):
        return f"{self._git_repo}/releases"

    def _get_release_info(
        self, *, version_toml_url: str, timeout: int = 5
    ) -> ReleaseInfo:
        try:
            content = fetch_remote_content(file_url=version_toml_url, timeout=timeout)
            data = tomllib.loads(content)

            latest_version = data.get("project", {}).get("version")

            if not latest_version:
                raise ValueError("Version is missing in the response.")

            metadata = data.get("tool", {}).get("app_metadata", {})

            return ReleaseInfo(
                version=latest_version,
                date=metadata.get("version", "No release date provided."),
                notes=metadata.get(
                    "release_notes", "Fixed minor bugs and improved stability."
                ),
            )
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"Failed to fetch release info: {e}")
            raise

    def _get_current_version(self) -> str:
        default_version = "0.0.0"
        config_toml_path = "Unknown path"
        try:
            config_toml_path = config.CONFIG_PATH
            with open(config_toml_path, "rb") as f:
                data = tomllib.load(f)
                return str(data.get("project", {}).get("version", default_version))

        except FileNotFoundError:
            logger.error(f"Version check failed: File not found at {config_toml_path}")
        except PermissionError:
            logger.error(
                f"Version check failed: Permission denied for {config_toml_path}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error reading version: {type(e).__name__} - {e}",
                exc_info=True,
            )
        return default_version

    def check_for_updates(self) -> UpdateCheckResult:
        version_toml_url=self._get_version_toml_url()
        try:
            latest_release = self._get_release_info(version_toml_url=version_toml_url,timeout=5)
            current_version = self._get_current_version()

            if version.parse(latest_release.version) > version.parse(current_version):
                return UpdateCheckResult(is_available=True, release=latest_release)

            return UpdateCheckResult(is_available=False)

        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return UpdateCheckResult(is_available=False, error_message=str(e))
