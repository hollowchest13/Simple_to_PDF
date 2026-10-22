import logging
from unittest.mock import MagicMock, patch

import pytest
import requests
import tomllib

from simple_to_pdf.core import version as mod
from simple_to_pdf.core.models import ReleaseInfo

VersionController = mod.VersionController

URL = "https://raw.githubusercontent.com/user/repo/main/pyproject.toml"


@pytest.fixture
def controller():
    return VersionController(git_repo="repo", git_user="user")


def make_release(version: str = "1.2.0") -> ReleaseInfo:
    return ReleaseInfo(version=version, date="2024-01-01", notes="notes")


class TestUrls:
    def test_version_toml_url(self, controller):
        assert controller._get_version_toml_url() == URL

    def test_release_url_is_full_github_url(self, controller):
        assert controller._get_release_url() == "https://github.com/user/repo/releases"


class TestGetReleaseInfo:
    def test_parses_version_and_metadata(self, controller):
        content = (
            '[project]\nversion = "1.2.3"\n\n'
            '[tool.app_metadata]\nrelease_date = "2024-05-01"\n'
            'release_notes = "Big changes"\n'
        )

        with patch.object(mod, "fetch_remote_content", return_value=content) as fetch:
            info = controller._get_release_info(version_toml_url=URL)

        fetch.assert_called_once_with(file_url=URL, timeout=5)
        assert info.version == "1.2.3"
        assert info.date == "2024-05-01"
        assert info.notes == "Big changes"

    def test_version_key_in_metadata_is_not_used_as_date(self, controller):
        content = (
            '[project]\nversion = "1.0.0"\n\n[tool.app_metadata]\nversion = "9.9.9"\n'
        )

        with patch.object(mod, "fetch_remote_content", return_value=content):
            info = controller._get_release_info(version_toml_url=URL)

        assert info.date == "No release date provided."

    def test_uses_defaults_when_metadata_missing(self, controller):
        content = '[project]\nversion = "1.0.0"\n'

        with patch.object(mod, "fetch_remote_content", return_value=content):
            info = controller._get_release_info(version_toml_url=URL)

        assert info.version == "1.0.0"
        assert info.date == "No release date provided."
        assert info.notes == "Fixed minor bugs and improved stability."

    def test_custom_timeout_is_passed_through(self, controller):
        with patch.object(
            mod, "fetch_remote_content", return_value='[project]\nversion = "1.0.0"\n'
        ) as fetch:
            controller._get_release_info(version_toml_url=URL, timeout=30)

        fetch.assert_called_once_with(file_url=URL, timeout=30)

    @pytest.mark.parametrize(
        "content",
        [
            '[project]\nname = "x"\n',
            '[project]\nversion = ""\n',
            '[tool.something]\nkey = "value"\n',
            "",
        ],
        ids=["no_version", "empty_version", "no_project", "empty_document"],
    )
    def test_missing_version_raises_value_error(self, controller, content, caplog):
        with (
            patch.object(mod, "fetch_remote_content", return_value=content),
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="Version is missing"),
        ):
            controller._get_release_info(version_toml_url=URL)

        assert "Failed to fetch release info" in caplog.text

    def test_network_error_is_logged_and_reraised(self, controller, caplog):
        error = requests.ConnectionError("offline")

        with (
            patch.object(mod, "fetch_remote_content", side_effect=error),
            caplog.at_level(logging.ERROR),
            pytest.raises(requests.ConnectionError),
        ):
            controller._get_release_info(version_toml_url=URL)

        assert "offline" in caplog.text

    def test_invalid_toml_is_logged_and_reraised(self, controller, caplog):
        with (
            patch.object(
                mod, "fetch_remote_content", return_value="this is [not valid toml"
            ),
            caplog.at_level(logging.ERROR),
            pytest.raises(tomllib.TOMLDecodeError),
        ):
            controller._get_release_info(version_toml_url=URL)

        assert "Failed to fetch release info" in caplog.text


class TestGetCurrentVersion:
    def test_reads_version_from_config(self, controller, tmp_path):
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text('[project]\nversion = "2.5.1"\n')

        with patch.object(mod.config, "CONFIG_PATH", config_file):
            assert controller._get_current_version() == "2.5.1"

    def test_non_string_version_is_converted_to_str(self, controller, tmp_path):
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[project]\nversion = 3\n")

        with patch.object(mod.config, "CONFIG_PATH", config_file):
            assert controller._get_current_version() == "3"

    @pytest.mark.parametrize(
        "content",
        ['[project]\nname = "x"\n', "[tool.x]\na = 1\n", ""],
        ids=["no_version", "no_project", "empty_file"],
    )
    def test_missing_version_returns_default(self, controller, tmp_path, content):
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(content)

        with patch.object(mod.config, "CONFIG_PATH", config_file):
            assert controller._get_current_version() == "0.0.0"

    def test_missing_file_returns_default_and_logs(self, controller, tmp_path, caplog):
        with (
            patch.object(mod.config, "CONFIG_PATH", tmp_path / "nope.toml"),
            caplog.at_level(logging.ERROR),
        ):
            result = controller._get_current_version()

        assert result == "0.0.0"
        assert "File not found" in caplog.text

    def test_permission_error_returns_default_and_logs(
        self, controller, tmp_path, caplog
    ):
        with (
            patch.object(mod.config, "CONFIG_PATH", tmp_path / "x.toml"),
            patch("builtins.open", side_effect=PermissionError),
            caplog.at_level(logging.ERROR),
        ):
            result = controller._get_current_version()

        assert result == "0.0.0"
        assert "Permission denied" in caplog.text

    def test_invalid_toml_returns_default_and_logs(self, controller, tmp_path, caplog):
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[project\nversion = ")

        with (
            patch.object(mod.config, "CONFIG_PATH", config_file),
            caplog.at_level(logging.ERROR),
        ):
            result = controller._get_current_version()

        assert result == "0.0.0"
        assert "Unexpected error reading version" in caplog.text


class TestCheckForUpdates:
    @pytest.fixture
    def env(self, controller):
        controller._get_release_info = MagicMock()
        controller._get_current_version = MagicMock()
        return controller

    def test_update_available(self, env):
        latest = make_release("1.2.0")
        env._get_release_info.return_value = latest
        env._get_current_version.return_value = "1.1.0"

        result = env.check_for_updates()

        env._get_release_info.assert_called_once_with(version_toml_url=URL, timeout=5)
        assert result.is_available is True
        assert result.release is latest

    @pytest.mark.parametrize(
        ("latest", "current", "expected"),
        [
            ("1.10.0", "1.9.0", True),
            ("2.0.0", "1.99.99", True),
            ("1.0.0", "1.0.0rc1", True),
            ("1.0.0rc1", "0.9.0", True),
            ("1.2.0", "0.0.0", True),
            ("1.2.0", "1.2.0", False),
            ("1.1.0", "1.2.0", False),
            ("1.0.0rc1", "1.0.0", False),
            ("1.9.0", "1.10.0", False),
        ],
    )
    def test_version_comparison_is_semantic(self, env, latest, current, expected):
        env._get_release_info.return_value = make_release(latest)
        env._get_current_version.return_value = current

        result = env.check_for_updates()

        assert result.is_available is expected

    def test_no_update_has_no_release_and_no_error(self, env):
        env._get_release_info.return_value = make_release("1.0.0")
        env._get_current_version.return_value = "1.0.0"

        result = env.check_for_updates()

        assert result.is_available is False
        assert result.release is None
        assert result.error_message is None

    def test_fetch_error_is_returned_as_error_message(self, env, caplog):
        env._get_release_info.side_effect = requests.Timeout("timed out")

        with caplog.at_level(logging.ERROR):
            result = env.check_for_updates()

        assert result.is_available is False
        assert result.error_message == "timed out"
        assert "Update check failed" in caplog.text
        env._get_current_version.assert_not_called()

    def test_invalid_remote_version_is_returned_as_error(self, env):
        env._get_release_info.return_value = make_release("not-a-version")
        env._get_current_version.return_value = "1.0.0"

        result = env.check_for_updates()

        assert result.is_available is False
        assert result.error_message

    def test_invalid_local_version_is_returned_as_error(self, env):
        env._get_release_info.return_value = make_release("1.0.0")
        env._get_current_version.return_value = "garbage"

        result = env.check_for_updates()

        assert result.is_available is False
        assert result.error_message
