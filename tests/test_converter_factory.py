import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import simple_to_pdf.converters.converter_factory as cf  # <-- поправте шлях

WIN_PF = r"C:\Program Files\LibreOffice\program\soffice.exe"
WIN_PF86 = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"


def _set_os(monkeypatch, name: str) -> None:
    monkeypatch.setattr(cf.platform, "system", lambda: name)


def _patch_existing_windows_paths(monkeypatch, existing: set[str]) -> None:
    """Path.exists() for paths on C:\\ returns True only for `existing`."""
    real_exists = Path.exists

    def fake_exists(self, *args, **kwargs):
        text = str(self)
        if text.startswith("C:"):
            return text in existing
        return real_exists(self, *args, **kwargs)

    monkeypatch.setattr(Path, "exists", fake_exists)


@pytest.fixture
def factory() -> cf.ConverterFactory:
    return cf.ConverterFactory()


@pytest.fixture
def strategies(factory, monkeypatch) -> SimpleNamespace:
    """Replaces three _try_* methods; by default, each successfully creates the converter."""
    mocks = SimpleNamespace(
        ms=MagicMock(name="ms_office"),
        libre=MagicMock(name="libre_office"),
        image=MagicMock(name="image_only"),
    )
    monkeypatch.setattr(factory, "_try_ms_office", mocks.ms)
    monkeypatch.setattr(factory, "_try_libre_office", mocks.libre)
    monkeypatch.setattr(factory, "_try_image_only", mocks.image)
    return mocks


class TestGetConverter:
    def test_windows_prefers_ms_office(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Windows")

        result = factory.get_converter()

        assert result is strategies.ms.return_value
        strategies.libre.assert_not_called()
        strategies.image.assert_not_called()

    def test_windows_falls_back_to_libre_office(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Windows")
        strategies.ms.side_effect = RuntimeError("no office")

        result = factory.get_converter()

        assert result is strategies.libre.return_value
        strategies.image.assert_not_called()

    def test_windows_falls_back_to_image_only(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Windows")
        strategies.ms.side_effect = RuntimeError("no office")
        strategies.libre.side_effect = FileNotFoundError("no soffice")

        result = factory.get_converter()

        assert result is strategies.image.return_value

    def test_linux_skips_ms_office(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Linux")

        result = factory.get_converter()

        assert result is strategies.libre.return_value
        strategies.ms.assert_not_called()
        strategies.image.assert_not_called()

    def test_linux_falls_back_to_image_only(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Linux")
        strategies.libre.side_effect = FileNotFoundError("no soffice")

        result = factory.get_converter()

        assert result is strategies.image.return_value
        strategies.ms.assert_not_called()

    def test_other_os_uses_image_only(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Darwin")

        result = factory.get_converter()

        assert result is strategies.image.return_value
        strategies.ms.assert_not_called()
        strategies.libre.assert_not_called()

    def test_raises_when_no_converter_available(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Windows")
        for mock in (strategies.ms, strategies.libre, strategies.image):
            mock.side_effect = RuntimeError("fail")

        with pytest.raises(RuntimeError, match="Could not initialize any converter"):
            factory.get_converter()

        strategies.ms.assert_called_once()
        strategies.libre.assert_called_once()
        strategies.image.assert_called_once()

    def test_chunk_size_is_passed_to_strategy(self, factory, strategies, monkeypatch):
        _set_os(monkeypatch, "Linux")
        factory.chunk_size = 7

        factory.get_converter()

        strategies.libre.assert_called_once_with(chunk_size=7)


class TestFindSofficeWindows:
    def test_prefers_path_over_standard_folders(self, factory, monkeypatch):
        monkeypatch.setattr(cf.shutil, "which", lambda name: r"D:\tools\soffice.exe")
        _patch_existing_windows_paths(monkeypatch, {WIN_PF, WIN_PF86})

        assert factory._find_soffice_windows() == r"D:\tools\soffice.exe"

    def test_finds_in_program_files(self, factory, monkeypatch):
        monkeypatch.setattr(cf.shutil, "which", lambda name: None)
        _patch_existing_windows_paths(monkeypatch, {WIN_PF})

        assert factory._find_soffice_windows() == WIN_PF

    def test_finds_in_program_files_x86(self, factory, monkeypatch):
        monkeypatch.setattr(cf.shutil, "which", lambda name: None)
        _patch_existing_windows_paths(monkeypatch, {WIN_PF86})

        assert factory._find_soffice_windows() == WIN_PF86

    def test_program_files_wins_over_x86(self, factory, monkeypatch):
        monkeypatch.setattr(cf.shutil, "which", lambda name: None)
        _patch_existing_windows_paths(monkeypatch, {WIN_PF, WIN_PF86})

        assert factory._find_soffice_windows() == WIN_PF

    def test_raises_when_not_found(self, factory, monkeypatch):
        monkeypatch.setattr(cf.shutil, "which", lambda name: None)
        _patch_existing_windows_paths(monkeypatch, set())

        with pytest.raises(FileNotFoundError, match="LibreOffice not found"):
            factory._find_soffice_windows()


class TestGetLibrePath:
    def test_custom_path_has_priority(self, factory, monkeypatch):
        which = MagicMock()
        find_windows = MagicMock()
        monkeypatch.setattr(cf.shutil, "which", which)
        monkeypatch.setattr(factory, "_find_soffice_windows", find_windows)

        assert factory._get_libre_path(custom_path="/opt/soffice") == "/opt/soffice"
        which.assert_not_called()
        find_windows.assert_not_called()

    def test_windows_uses_windows_search(self, factory, monkeypatch):
        _set_os(monkeypatch, "Windows")
        monkeypatch.setattr(
            factory, "_find_soffice_windows", MagicMock(return_value=WIN_PF)
        )

        assert factory._get_libre_path() == WIN_PF

    def test_linux_uses_which(self, factory, monkeypatch):
        _set_os(monkeypatch, "Linux")
        which = MagicMock(return_value="/usr/bin/soffice")
        monkeypatch.setattr(cf.shutil, "which", which)

        assert factory._get_libre_path() == "/usr/bin/soffice"
        which.assert_called_once_with("soffice")

    def test_linux_returns_none_when_missing(self, factory, monkeypatch):
        _set_os(monkeypatch, "Linux")
        monkeypatch.setattr(cf.shutil, "which", lambda name: None)

        assert factory._get_libre_path() is None


class TestTryLibreOffice:
    def test_raises_when_soffice_not_found(self, factory, monkeypatch):
        monkeypatch.setattr(factory, "_get_libre_path", lambda **kw: None)

        with pytest.raises(FileNotFoundError, match="soffice"):
            factory._try_libre_office(chunk_size=10)

    def test_creates_converter_with_path_and_chunk_size(self, factory, monkeypatch):
        monkeypatch.setattr(factory, "_get_libre_path", lambda **kw: "/usr/bin/soffice")
        fake_module = types.ModuleType("simple_to_pdf.converters.lib_office_converter")
        fake_module.LibreOfficeConverter = MagicMock()  # type: ignore
        monkeypatch.setitem(
            sys.modules,
            "simple_to_pdf.converters.lib_office_converter",
            fake_module,
        )

        result = factory._try_libre_office(chunk_size=7)

        fake_module.LibreOfficeConverter.assert_called_once_with(
            soffice_path="/usr/bin/soffice", chunk_size=7
        )
        assert result is fake_module.LibreOfficeConverter.return_value
        assert factory.soffice_path == "/usr/bin/soffice"
