import json
import logging
import webbrowser
from tkinter import messagebox
from typing import Callable, List

import requests
import tomllib
from packaging import version

from simple_to_pdf.core.config import get_project_config_path
from simple_to_pdf.core.models import ReleaseInfo
from simple_to_pdf.utils.network import fetch_remote_content

logger = logging.getLogger(__name__)


class VersionController:
    def __init__(self, *, git_repo: str, git_user: str):
        self._git_repo: str = git_repo
        self._git_user: str = git_user

    def _get_version_json_url(self) -> str:
        version_json_url = f"https://raw.githubusercontent.com/{self._git_user}/{self._git_repo}/main/src/simple_to_pdf/cli/version.json"
        return version_json_url

    def _get_version_toml_url(self) -> str:
        version_toml_url = f"https://raw.githubusercontent.com/{self._git_user}/{self._git_repo}/main/pyproject.toml"
        return version_toml_url

    def _get_release_url(self):
        return f"{self._git_repo}/releases"

    def _get_release_info_from_json(
        self, *, version_json_url, timeout: int = 5
    ) -> ReleaseInfo:
        try:
            content = fetch_remote_content(file_url=version_json_url, timeout=timeout)
            data = json.loads(content)

            latest_version = data.get("version")
            if not latest_version:
                raise ValueError("Version is missing in the response.")
            else:
                return ReleaseInfo(
                    version=latest_version,
                    date=data.get("release_date", "No release date provided."),
                    notes=data.get("release_notes", "No release notes provided."),
                )
        except (requests.RequestException, ValueError) as e:
            logger.error(f"Failed to fetch release info: {e}")
            raise

    def _get_release_info_from_toml(
        self, *, version_toml_url: str, timeout: int = 5
    ) -> ReleaseInfo:
        try:
            content = fetch_remote_content(file_url=version_toml_url, timeout=timeout)
            data = tomllib.loads(content)
            
            # Access the version in [project] section
            latest_version = data.get("project", {}).get("version")
            
            if not latest_version:
                raise ValueError("Version is missing in the response.")
            
            # Access nested [tool.app_metadata] section
            metadata = data.get("tool", {}).get("app_metadata", {})
            
            return ReleaseInfo(
                version=latest_version,
                # Use parentheses () for .get and access the metadata dictionary
                date=metadata.get("version", "Unknown"),
                notes=metadata.get("release_notes", "No notes"),
            )
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"Failed to fetch release info: {e}")
            raise

    def _get_release_info(self, *, timeout: int = 5) -> ReleaseInfo:
        version_json_url: str = self._get_version_toml_url()
        version_toml_url: str = self._get_version_toml_url()
        strategies: List[Callable[[], ReleaseInfo]] = [
            lambda: self._get_release_info_from_json(
                version_json_url=version_json_url, timeout=timeout
            ),
            lambda: self._get_release_info_from_toml(
                version_toml_url=version_toml_url, timeout=timeout
            ),
        ]
        for strategy in strategies:
            try:
                release: ReleaseInfo = strategy()
                return release
            except Exception as e:
                err_type = type(e).__name__
                err_msg = str(e)
                logger.warning(f"Error details: [{err_type}] {err_msg}", exc_info=True)
        raise RuntimeError("All update fetch strategies failed. Check network or URLs.")
        

    def _get_current_version(self) -> str:

        default_version = "0.0.0"
        config_toml_path=None
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

    def check_updates(self):
        """Fetches the latest version info from GitHub and prompts for update."""
        try:
            latest_release: ReleaseInfo = self._get_release_info(timeout=5)
            current_version: str = self._get_current_version()
            release_url = self._get_release_url()

            if not latest_release.version:
                raise ValueError("Version is missing in the response.")

            if version.parse(latest_release.version) <= version.parse(current_version):
                messagebox.showinfo(
                    "Update Check",
                    f"You are up to date!\nVersion {current_version} is the latest.",
                )
            else:
                message = (
                    f"A new version is available: {latest_release.version}\n\n"
                    f"What's new:\n{latest_release.notes}\n\n"
                    "Would you like to visit the download page?"
                )
                if messagebox.askyesno("Update Available", message):
                    webbrowser.open(release_url)

        except requests.exceptions.RequestException as e:
            logger.error(f"Update check failed (Network error): {e}")
            messagebox.showerror(
                "Update Error",
                "Could not connect to the update server.\nPlease check your internet connection.",
            )
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            messagebox.showerror("Update Error", f"An unexpected error occurred:\n{e}")
