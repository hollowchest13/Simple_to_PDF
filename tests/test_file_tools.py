from pathlib import Path
from unittest.mock import MagicMock

import pytest

import simple_to_pdf.utils.file_tools as ft


@pytest.fixture
def msgbox(monkeypatch) -> MagicMock:
    """Overrides tkinter.messagebox to not open real windows."""
    mock = MagicMock()
    monkeypatch.setattr(ft, "messagebox", mock)
    return mock


@pytest.fixture
def dialog(monkeypatch) -> MagicMock:
    """Replaces tkinter.filedialog."""
    mock = MagicMock()
    monkeypatch.setattr(ft, "filedialog", mock)
    return mock


class TestFileToolKit:
    def test_write_bytes_creates_parents_and_returns_resolved_path(self, tmp_path):
        target = tmp_path / "a" / "b" / "out.bin"

        result = ft.FileToolKit.write_bytes(file_path=target, bytes_data=b"abc")

        assert result == target.resolve()
        assert target.read_bytes() == b"abc"

    def test_read_text_file_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="File missing"):
            ft.FileToolKit.read_text_file(file_path=tmp_path / "nope.txt")


class TestFileCategory:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("a.pdf", "pdf"),
            ("a.xlsx", "table"),
            ("a.docx", "document"),
            ("a.pptx", "presentation"),
            ("a.png", "image"),
            ("A.PDF", "pdf"),  # регістр не важливий
        ],
    )
    def test_known_extensions(self, name, expected):
        assert ft.get_file_category(Path(name)) == expected

    @pytest.mark.parametrize("name", ["a.exe", "noext"])
    def test_unknown_returns_none(self, name):
        assert ft.get_file_category(Path(name)) is None

    def test_no_extension_belongs_to_two_categories(self):
        seen: dict[str, str] = {}
        for category, exts in ft.GLOBAL_EXTENSIONS.items():
            for ext in exts:
                assert ext not in seen, f"{ext} є і в {seen[ext]}, і в {category}"
                seen[ext] = category


class TestGetText:
    def test_returns_file_content(self, tmp_path, msgbox):
        f = tmp_path / "c.txt"
        f.write_text("зміст", encoding="utf-8")

        assert ft.get_text(file_name="Config", file_path=str(f)) == "зміст"
        msgbox.showwarning.assert_not_called()
        msgbox.showerror.assert_not_called()

    def test_missing_file_shows_warning_and_returns_none(self, tmp_path, msgbox):
        result = ft.get_text(
            file_name="Config", file_path=str(tmp_path / "missing.txt")
        )

        assert result is None
        msgbox.showwarning.assert_called_once_with("Warning", "Config file not found")
        msgbox.showerror.assert_not_called()

    def test_unreadable_file_shows_error_and_returns_none(self, tmp_path, msgbox):
        f = tmp_path / "bad.txt"
        f.write_bytes(b"\xff\xfe\xfa")  # невалідний UTF-8

        result = ft.get_text(file_name="Config", file_path=str(f))

        assert result is None
        msgbox.showerror.assert_called_once()
        title, message = msgbox.showerror.call_args.args
        assert title == "Error"
        assert message.startswith("Failed to read Config")


class TestGetFiles:
    def test_multiple_uses_askopenfilenames(self, dialog):
        dialog.askopenfilenames.return_value = ("a.pdf", "b.pdf")

        assert ft.get_files() == ("a.pdf", "b.pdf")
        dialog.askopenfilename.assert_not_called()

    def test_single_uses_askopenfilename(self, dialog):
        dialog.askopenfilename.return_value = "a.pdf"

        assert ft.get_files(multiple=False) == "a.pdf"
        dialog.askopenfilenames.assert_not_called()

    def test_raw_extensions_are_converted_to_filters(self, dialog):
        ft.get_files(filetypes=(".pdf", ".docx"))

        filters = dialog.askopenfilenames.call_args.kwargs["filetypes"]
        assert filters[0] == ("All supported types", "*.pdf *.docx")
        assert [mask for _, mask in filters[1:]] == ["*.pdf", "*.docx"]

    def test_ready_made_filters_are_passed_as_is(self, dialog):
        custom = [("Images", "*.png *.jpg"), ("All", "*.*")]

        ft.get_files(filetypes=custom, multiple=False)

        assert dialog.askopenfilename.call_args.kwargs["filetypes"] is custom


class TestGetUniquePath:
    def test_free_path_is_returned_and_parent_created(self, tmp_path):
        target = tmp_path / "x" / "file.pdf"

        assert ft.get_unique_path(target) == target
        assert target.parent.is_dir()
        assert not target.exists()

    def test_adds_counter_if_exists(self, tmp_path):
        (tmp_path / "file.pdf").write_text("x")

        assert ft.get_unique_path(tmp_path / "file.pdf") == tmp_path / "file(1).pdf"

    def test_skips_taken_counters(self, tmp_path):
        for name in ("file.pdf", "file(1).pdf", "file(2).pdf"):
            (tmp_path / name).write_text("x")

        assert ft.get_unique_path(tmp_path / "file.pdf") == tmp_path / "file(3).pdf"

    def test_multi_dot_name_keeps_full_stem(self, tmp_path):
        (tmp_path / "report.final.pdf").write_text("x")

        result = ft.get_unique_path(tmp_path / "report.final.pdf")

        assert result == tmp_path / "report.final(1).pdf"
