import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pypdf import PdfReader, PdfWriter

from simple_to_pdf.pdf.page_extractor import PageExtractor

TOTAL_PAGES = 5


def page_width(page_number: int) -> int:
    """A unique width for each page so you can tell them apart."""
    return 100 + page_number * 10


def widths(pdf_path: Path) -> list[int]:
    return [int(p.mediabox.width) for p in PdfReader(pdf_path).pages]


@pytest.fixture
def source_pdf(tmp_path: Path) -> Path:
    """5-page PDF; page width N = 100 + N * 10."""
    path = tmp_path / "source.pdf"
    writer = PdfWriter()
    for n in range(1, TOTAL_PAGES + 1):
        writer.add_blank_page(width=page_width(n), height=200)
    with path.open("wb") as f:
        writer.write(f)
    return path


@pytest.fixture
def extractor(monkeypatch) -> PageExtractor:
    ext = PageExtractor()
    ext.callback = MagicMock()
    ext.check_stop = MagicMock()

    module = sys.modules[PageExtractor.__module__]
    monkeypatch.setattr(module, "get_unique_path", lambda p: p)
    return ext


class TestExtractPages:
    def test_extracts_requested_pages_in_given_order(
        self, extractor, source_pdf, tmp_path
    ):
        out = tmp_path / "out.pdf"

        result = extractor.extract_pages(
            input_file=source_pdf, pages_to_extract=[3, 1, 5], output_file=out
        )

        assert result == out
        assert out.exists()
        assert widths(out) == [page_width(3), page_width(1), page_width(5)]

    def test_single_page(self, extractor, source_pdf, tmp_path):
        out = tmp_path / "out.pdf"

        extractor.extract_pages(
            input_file=source_pdf, pages_to_extract=[2], output_file=out
        )

        assert widths(out) == [page_width(2)]

    def test_duplicate_pages_are_allowed(self, extractor, source_pdf, tmp_path):
        out = tmp_path / "out.pdf"

        extractor.extract_pages(
            input_file=source_pdf, pages_to_extract=[2, 2], output_file=out
        )

        assert widths(out) == [page_width(2)] * 2

    def test_all_pages(self, extractor, source_pdf, tmp_path):
        out = tmp_path / "out.pdf"

        extractor.extract_pages(
            input_file=source_pdf,
            pages_to_extract=list(range(1, TOTAL_PAGES + 1)),
            output_file=out,
        )

        assert widths(out) == [page_width(n) for n in range(1, TOTAL_PAGES + 1)]

    def test_progress_callback_called_for_each_page(
        self, extractor, source_pdf, tmp_path
    ):
        extractor.extract_pages(
            input_file=source_pdf,
            pages_to_extract=[4, 2],
            output_file=tmp_path / "out.pdf",
        )

        progress_calls = [
            c for c in extractor.callback.call_args_list if c.args[0] == "progress"
        ]
        assert len(progress_calls) == 2
        assert progress_calls[0].kwargs == {
            "stage": "extracting",
            "mode": "determinate",
            "current": 1,
            "total": 2,
            "filename": "page 4",
        }
        assert progress_calls[1].kwargs["current"] == 2
        assert progress_calls[1].kwargs["filename"] == "page 2"

    def test_done_status_callback_is_last_and_contains_path(
        self, extractor, source_pdf, tmp_path
    ):
        out = tmp_path / "out.pdf"

        extractor.extract_pages(
            input_file=source_pdf, pages_to_extract=[1], output_file=out
        )

        last = extractor.callback.call_args_list[-1]
        assert last.args == ("status",)
        assert last.kwargs == {
            "key": "extracting.done",
            "status": "info",
            "path": str(out),
        }

    def test_check_stop_called_for_each_page(self, extractor, source_pdf, tmp_path):
        extractor.extract_pages(
            input_file=source_pdf,
            pages_to_extract=[1, 2, 3],
            output_file=tmp_path / "out.pdf",
        )

        assert extractor.check_stop.call_count == 3

    def test_uses_unique_path_for_output(
        self, extractor, source_pdf, tmp_path, monkeypatch
    ):
        requested = tmp_path / "out.pdf"
        unique = tmp_path / "out (1).pdf"
        module = sys.modules[PageExtractor.__module__]
        get_unique = MagicMock(return_value=unique)
        monkeypatch.setattr(module, "get_unique_path", get_unique)

        result = extractor.extract_pages(
            input_file=source_pdf, pages_to_extract=[1], output_file=requested
        )

        get_unique.assert_called_once_with(requested)
        assert result == unique
        assert unique.exists()
        assert not requested.exists()
        assert extractor.callback.call_args_list[-1].kwargs["path"] == str(unique)

    def test_does_not_overwrite_existing_file(
        self, extractor, source_pdf, tmp_path, monkeypatch
    ):
        existing = tmp_path / "out.pdf"
        existing.write_bytes(b"original")
        unique = tmp_path / "out (1).pdf"
        module = sys.modules[PageExtractor.__module__]
        monkeypatch.setattr(module, "get_unique_path", lambda p: unique)

        extractor.extract_pages(
            input_file=source_pdf, pages_to_extract=[1], output_file=existing
        )

        assert existing.read_bytes() == b"original"
        assert unique.exists()

    def test_page_above_range_is_skipped_and_error_reported(
        self, extractor, source_pdf, tmp_path
    ):
        out = tmp_path / "out.pdf"

        extractor.extract_pages(
            input_file=source_pdf,
            pages_to_extract=[1, TOTAL_PAGES + 1, 2],
            output_file=out,
        )

        assert widths(out) == [page_width(1), page_width(2)]

        error_calls = [
            c
            for c in extractor.callback.call_args_list
            if c.kwargs.get("status") == "error"
        ]
        assert len(error_calls) == 1
        kwargs = error_calls[0].kwargs
        assert kwargs["key"] == "extracting.error"
        assert kwargs["page_number"] == TOTAL_PAGES + 1
        assert isinstance(kwargs["error"], IndexError)

    def test_out_of_range_page_logs_error(
        self, extractor, source_pdf, tmp_path, caplog
    ):
        with caplog.at_level("ERROR"):
            extractor.extract_pages(
                input_file=source_pdf,
                pages_to_extract=[TOTAL_PAGES + 1],
                output_file=tmp_path / "out.pdf",
            )

        assert f"Page {TOTAL_PAGES + 1} is out of range" in caplog.text

    def test_no_progress_for_skipped_page(self, extractor, source_pdf, tmp_path):
        extractor.extract_pages(
            input_file=source_pdf,
            pages_to_extract=[TOTAL_PAGES + 1],
            output_file=tmp_path / "out.pdf",
        )

        progress_calls = [
            c for c in extractor.callback.call_args_list if c.args[0] == "progress"
        ]
        assert progress_calls == []

    def test_cancellation_propagates_and_no_file_written(
        self, extractor, source_pdf, tmp_path, caplog
    ):
        out = tmp_path / "out.pdf"
        extractor.check_stop.side_effect = [None, InterruptedError()]

        with caplog.at_level("INFO"), pytest.raises(InterruptedError):
            extractor.extract_pages(
                input_file=source_pdf, pages_to_extract=[1, 2, 3], output_file=out
            )

        assert not out.exists()
        assert "successfully cancelled" in caplog.text
        # done status should not be sent
        assert not any(
            c.kwargs.get("key") == "extracting.done"
            for c in extractor.callback.call_args_list
        )

    def test_writer_is_closed_on_success(
        self, extractor, source_pdf, tmp_path, monkeypatch
    ):
        closed = []
        module = sys.modules[PageExtractor.__module__]

        class TrackingWriter(PdfWriter):
            def close(self):
                closed.append(True)
                super().close()

        monkeypatch.setattr(module, "PdfWriter", TrackingWriter)

        extractor.extract_pages(
            input_file=source_pdf,
            pages_to_extract=[1],
            output_file=tmp_path / "out.pdf",
        )

        assert closed == [True]

    def test_writer_is_closed_on_cancellation(
        self, extractor, source_pdf, tmp_path, monkeypatch
    ):
        closed = []
        module = sys.modules[PageExtractor.__module__]

        class TrackingWriter(PdfWriter):
            def close(self):
                closed.append(True)
                super().close()

        monkeypatch.setattr(module, "PdfWriter", TrackingWriter)
        extractor.check_stop.side_effect = InterruptedError()

        with pytest.raises(InterruptedError):
            extractor.extract_pages(
                input_file=source_pdf,
                pages_to_extract=[1],
                output_file=tmp_path / "out.pdf",
            )

        assert closed == [True]

    def test_missing_input_file_raises(self, extractor, tmp_path):
        with pytest.raises(FileNotFoundError):
            extractor.extract_pages(
                input_file=tmp_path / "missing.pdf",
                pages_to_extract=[1],
                output_file=tmp_path / "out.pdf",
            )

    def test_empty_page_list_produces_no_pages(self, extractor, source_pdf, tmp_path):
        """Without validation, extract_pages with an empty list writes an empty PDF
        (or drops in pypdf). We fix the current behavior: validation is it
        responsibility of validate_pages."""
        out = tmp_path / "out.pdf"

        try:
            extractor.extract_pages(
                input_file=source_pdf, pages_to_extract=[], output_file=out
            )
        except Exception:  # noqa: BLE001
            pytest.skip("pypdf does not allow you to save a PDF without pages")
        else:
            assert len(PdfReader(out).pages) == 0


class TestValidatePages:
    def test_valid_pages_do_not_raise(self, extractor, source_pdf):
        extractor.validate_pages(input_path=source_pdf, pages_to_extract=[1, 3, 5])

    def test_boundaries_are_valid(self, extractor, source_pdf):
        extractor.validate_pages(
            input_path=source_pdf, pages_to_extract=[1, TOTAL_PAGES]
        )

    def test_returns_none(self, extractor, source_pdf):
        assert (
            extractor.validate_pages(input_path=source_pdf, pages_to_extract=[1])
            is None
        )

    @pytest.mark.parametrize("pages", [None, []])
    def test_empty_or_none_raises(self, extractor, source_pdf, pages):
        with pytest.raises(ValueError, match="No pages selected"):
            extractor.validate_pages(input_path=source_pdf, pages_to_extract=pages)

    def test_missing_file_raises(self, extractor, tmp_path):
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            extractor.validate_pages(
                input_path=tmp_path / "missing.pdf", pages_to_extract=[1]
            )

    def test_empty_pages_checked_before_file_existence(self, extractor, tmp_path):
        with pytest.raises(ValueError, match="No pages selected"):
            extractor.validate_pages(
                input_path=tmp_path / "missing.pdf", pages_to_extract=[]
            )

    @pytest.mark.parametrize("bad_page", [0, -1, TOTAL_PAGES + 1, 100])
    def test_out_of_range_raises(self, extractor, source_pdf, bad_page):
        with pytest.raises(ValueError, match="Invalid page numbers"):
            extractor.validate_pages(
                input_path=source_pdf, pages_to_extract=[1, bad_page]
            )

    def test_error_mentions_actual_total(self, extractor, source_pdf):
        with pytest.raises(ValueError, match=f"only {TOTAL_PAGES} pages"):
            extractor.validate_pages(
                input_path=source_pdf, pages_to_extract=[TOTAL_PAGES + 1]
            )

    def test_error_lists_original_invalid_page_numbers(self, extractor, source_pdf):
        with pytest.raises(ValueError) as exc_info:
            extractor.validate_pages(input_path=source_pdf, pages_to_extract=[1, 7, 9])

        assert "[7, 9]" in str(exc_info.value)
