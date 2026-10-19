# pyright: reportAttributeAccessIssue=false, reportArgumentType=false
import logging
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pypdf import PageObject, PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from simple_to_pdf.pdf.pdf_merger import PdfMerger

A4 = SimpleNamespace(size=(595, 842))  # заглушка для PageFormat
A4_W, A4_H = 595, 842
PAGE_HEIGHT = 200


# --------------------------------------------------------------------------
# Helpers and fixtures
# --------------------------------------------------------------------------
def make_pdf(path: Path, widths: list[float], height: float = PAGE_HEIGHT) -> Path:
    """A PDF where page N has a width of widths[N] (so it's easy to tell them apart)."""
    writer = PdfWriter()
    for w in widths:
        writer.add_blank_page(width=w, height=height)
    with path.open("wb") as f:
        writer.write(f)
    return path


def make_pdf_with_box(path: Path, box: tuple[float, float, float, float]) -> Path:
    """PDF with one page and arbitrary MediaBox [x0, y0, x1, y1]."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=1, height=1)
    page.mediabox = RectangleObject(box)
    with path.open("wb") as f:
        writer.write(f)
    return path


def item(index: int, path: Path) -> SimpleNamespace:
    """Stub for ConvertedFileItem."""
    return SimpleNamespace(index=index, converted_path=path)


def report(items: list, failed: int = 0) -> SimpleNamespace:
    """Stub for ProcessingReport."""
    return SimpleNamespace(documents=items, failed=failed)


def widths(pdf_path: Path) -> list[int]:
    return [round(float(p.mediabox.width)) for p in PdfReader(pdf_path).pages]


def sizes(pdf_path: Path) -> list[tuple[int, int]]:
    return [
        (round(float(p.mediabox.width)), round(float(p.mediabox.height)))
        for p in PdfReader(pdf_path).pages
    ]


def payloads(merger: PdfMerger, kind: str) -> list[dict]:
    """All dictionaries passed to _show_callback with a given message type."""
    return [
        c.args[1] for c in merger._show_callback.call_args_list if c.args[0] == kind
    ]


@pytest.fixture
def merger(monkeypatch) -> PdfMerger:
    m = PdfMerger()
    m._show_callback = MagicMock()
    m.check_stop = MagicMock()

    # By default, get_unique_path returns the path unchanged.
    module = sys.modules[PdfMerger.__module__]
    monkeypatch.setattr(module, "get_unique_path", lambda p: p)
    return m


@pytest.fixture
def merge_spy(monkeypatch) -> list:
    """Intercepts the Transformation with which _scale_and_append calls
    PageObject.merge_transformed_page, and does not perform the merge itself."""
    captured: list = []

    def fake_merge(self, page2, ctm, over=True, expand=False):
        captured.append(ctm)

    monkeypatch.setattr(PageObject, "merge_transformed_page", fake_merge)
    return captured


# --------------------------------------------------------------------------
# _scale_and_append
# --------------------------------------------------------------------------
class TestScaleAndAppend:
    def run(
        self, merger: PdfMerger, pdf: Path, fmt: SimpleNamespace | None = A4
    ) -> PdfWriter:
        writer = PdfWriter()
        merger._scale_and_append(
            reader=PdfReader(pdf), writer=writer, target_page_format=fmt
        )
        return writer

    def test_none_format_adds_nothing(self, merger, tmp_path):
        pdf = make_pdf(tmp_path / "a.pdf", [A4_W])

        writer = self.run(merger, pdf, fmt=None)

        assert len(writer.pages) == 0

    def test_page_with_correct_size_is_added_as_is(self, merger, tmp_path, merge_spy):
        pdf = make_pdf(tmp_path / "a.pdf", [A4_W], height=A4_H)

        writer = self.run(merger, pdf)

        assert merge_spy == []  # no transformation required
        assert len(writer.pages) == 1
        assert float(writer.pages[0].mediabox.width) == A4_W

    def test_landscape_page_with_correct_size_is_added_as_is(
        self, merger, tmp_path, merge_spy
    ):
        pdf = make_pdf(tmp_path / "a.pdf", [A4_H], height=A4_W)

        writer = self.run(merger, pdf)

        assert merge_spy == []
        assert len(writer.pages) == 1

    def test_format_size_order_does_not_matter(self, merger, tmp_path, merge_spy):
        pdf = make_pdf(tmp_path / "a.pdf", [A4_W], height=A4_H)
        reversed_fmt = SimpleNamespace(size=(A4_H, A4_W))

        writer = self.run(merger, pdf, fmt=reversed_fmt)

        assert merge_spy == []
        assert sizes_of(writer) == [(A4_W, A4_H)]

    def test_size_within_tolerance_is_added_as_is(self, merger, tmp_path, merge_spy):
        pdf = make_pdf(tmp_path / "a.pdf", [A4_W + 0.5], height=A4_H - 0.5)

        self.run(merger, pdf)

        assert merge_spy == []

    def test_size_outside_tolerance_is_rescaled(self, merger, tmp_path, merge_spy):
        pdf = make_pdf(tmp_path / "a.pdf", [A4_W + 2], height=A4_H)

        self.run(merger, pdf)

        assert len(merge_spy) == 1

    def test_small_portrait_page_is_scaled_up_and_centered(
        self, merger, tmp_path, merge_spy
    ):
        pdf = make_pdf(tmp_path / "a.pdf", [100], height=100)  # квадрат

        writer = self.run(merger, pdf)

        # square is considered portrait -> target 595x842
        assert sizes_of(writer) == [(A4_W, A4_H)]
        scale = A4_W / 100  # limited by width
        ty = (A4_H - 100 * scale) / 2
        assert merge_spy[0].ctm == pytest.approx((scale, 0, 0, scale, 0, ty))

    def test_landscape_page_gets_landscape_target(self, merger, tmp_path, merge_spy):
        pdf = make_pdf(tmp_path / "a.pdf", [200], height=100)

        writer = self.run(merger, pdf)

        assert sizes_of(writer) == [(A4_H, A4_W)]  # 842x595
        scale = min(A4_H / 200, A4_W / 100)
        ty = (A4_W - 100 * scale) / 2
        assert merge_spy[0].ctm == pytest.approx((scale, 0, 0, scale, 0, ty))

    def test_large_page_is_scaled_down(self, merger, tmp_path, merge_spy):
        pdf = make_pdf(tmp_path / "a.pdf", [1190], height=1684)  # 2x A4

        self.run(merger, pdf)

        assert merge_spy[0].ctm == pytest.approx((0.5, 0, 0, 0.5, 0, 0))

    def test_aspect_ratio_is_preserved(self, merger, tmp_path, merge_spy):
        pdf = make_pdf(tmp_path / "a.pdf", [300], height=100)

        self.run(merger, pdf)

        a, b, c, d, _, _ = merge_spy[0].ctm
        assert a == pytest.approx(d)
        assert (b, c) == (0, 0)

    def test_non_zero_mediabox_origin_is_compensated(self, merger, tmp_path, merge_spy):
        pdf = make_pdf_with_box(tmp_path / "a.pdf", (50, 50, 150, 150))

        self.run(merger, pdf)

        scale = A4_W / 100
        tx = (A4_W - 100 * scale) / 2 - 50 * scale
        ty = (A4_H - 100 * scale) / 2 - 50 * scale
        assert merge_spy[0].ctm == pytest.approx((scale, 0, 0, scale, tx, ty))

    def test_correct_size_but_offset_origin_is_not_added_as_is(
        self, merger, tmp_path, merge_spy
    ):
        pdf = make_pdf_with_box(tmp_path / "a.pdf", (10, 10, 10 + A4_W, 10 + A4_H))

        writer = self.run(merger, pdf)

        assert len(merge_spy) == 1
        assert merge_spy[0].ctm == pytest.approx((1, 0, 0, 1, -10, -10))
        assert sizes_of(writer) == [(A4_W, A4_H)]

    def test_all_pages_of_reader_are_processed(self, merger, tmp_path):
        pdf = make_pdf(tmp_path / "a.pdf", [100, 200, A4_W, 300])

        writer = self.run(merger, pdf)

        assert len(writer.pages) == 4
        # All pages must be A4 portrait (200x200 -> square, etc.)
        assert all((w, h) in {(A4_W, A4_H), (A4_H, A4_W)} for w, h in sizes_of(writer))


def sizes_of(writer: PdfWriter) -> list[tuple[int, int]]:
    return [
        (round(float(p.mediabox.width)), round(float(p.mediabox.height)))
        for p in writer.pages
    ]


# --------------------------------------------------------------------------
# merge_to_pdf — successful scenarios
# --------------------------------------------------------------------------
class TestMergeToPdf:
    @pytest.fixture
    def three_files(self, tmp_path) -> list[SimpleNamespace]:
        """Three files with page width 110 / 120 / 130 and indexes 1 / 2 / 3."""
        return [
            item(k, make_pdf(tmp_path / f"f{k}.pdf", [100 + k * 10])) for k in (1, 2, 3)
        ]

    def test_merges_all_files(self, merger, three_files, tmp_path):
        out = tmp_path / "out.pdf"

        result = merger.merge_to_pdf(
            conversion_rep=report(three_files), output_path=out
        )

        assert result == out
        assert widths(out) == [110, 120, 130]

    def test_files_are_merged_in_index_order(self, merger, three_files, tmp_path):
        out = tmp_path / "out.pdf"
        shuffled = [three_files[2], three_files[0], three_files[1]]

        merger.merge_to_pdf(conversion_rep=report(shuffled), output_path=out)

        assert widths(out) == [110, 120, 130]

    def test_multi_page_files_keep_all_pages(self, merger, tmp_path):
        a = make_pdf(tmp_path / "a.pdf", [110, 111])
        b = make_pdf(tmp_path / "b.pdf", [120, 121, 122])
        out = tmp_path / "out.pdf"

        merger.merge_to_pdf(
            conversion_rep=report([item(1, a), item(2, b)]), output_path=out
        )

        assert widths(out) == [110, 111, 120, 121, 122]

    def test_without_format_original_sizes_are_kept(
        self, merger, three_files, tmp_path
    ):
        out = tmp_path / "out.pdf"

        merger.merge_to_pdf(
            conversion_rep=report(three_files),
            target_page_format=None,
            output_path=out,
        )

        assert sizes(out) == [
            (110, PAGE_HEIGHT),
            (120, PAGE_HEIGHT),
            (130, PAGE_HEIGHT),
        ]

    def test_with_format_all_pages_are_scaled(self, merger, three_files, tmp_path):
        out = tmp_path / "out.pdf"

        merger.merge_to_pdf(
            conversion_rep=report(three_files),
            target_page_format=A4,
            output_path=out,
        )

        # Pages 110x200 .. 130x200 are portrait, so they all become 595x842
        assert sizes(out) == [(A4_W, A4_H)] * 3

    def test_uses_unique_output_path(self, merger, three_files, tmp_path, monkeypatch):
        requested = tmp_path / "out.pdf"
        unique = tmp_path / "out (1).pdf"
        module = sys.modules[PdfMerger.__module__]
        get_unique = MagicMock(return_value=unique)
        monkeypatch.setattr(module, "get_unique_path", get_unique)

        result = merger.merge_to_pdf(
            conversion_rep=report(three_files), output_path=requested
        )

        get_unique.assert_called_once_with(requested)
        assert result == unique
        assert unique.exists()
        assert not requested.exists()

    def test_does_not_overwrite_existing_file(
        self, merger, three_files, tmp_path, monkeypatch
    ):
        existing = tmp_path / "out.pdf"
        existing.write_bytes(b"original")
        module = sys.modules[PdfMerger.__module__]
        monkeypatch.setattr(
            module, "get_unique_path", lambda p: tmp_path / "out (1).pdf"
        )

        merger.merge_to_pdf(conversion_rep=report(three_files), output_path=existing)

        assert existing.read_bytes() == b"original"

    def test_progress_callbacks(self, merger, three_files, tmp_path):
        merger.merge_to_pdf(
            conversion_rep=report(three_files), output_path=tmp_path / "out.pdf"
        )

        progress = payloads(merger, "progress")
        assert progress[0] == {"stage": "merging", "mode": "indeterminate"}
        assert progress[1:] == [
            {
                "stage": "merging",
                "mode": "determinate",
                "current": i,
                "filename": f"f{i}.pdf",
                "total": 3,
            }
            for i in (1, 2, 3)
        ]

    def test_done_status_on_success(self, merger, three_files, tmp_path):
        merger.merge_to_pdf(
            conversion_rep=report(three_files), output_path=tmp_path / "out.pdf"
        )

        assert payloads(merger, "status") == [
            {"key": "merging.done", "status": "info", "success": 3, "failed": 0}
        ]

    def test_check_stop_called_per_file_and_before_write(
        self, merger, three_files, tmp_path
    ):
        merger.merge_to_pdf(
            conversion_rep=report(three_files), output_path=tmp_path / "out.pdf"
        )

        assert merger.check_stop.call_count == 3 + 1

    def test_writer_is_closed_on_success(
        self, merger, three_files, tmp_path, monkeypatch
    ):
        closed = []
        module = sys.modules[PdfMerger.__module__]

        class TrackingWriter(PdfWriter):
            def close(self):
                closed.append(True)
                super().close()

        monkeypatch.setattr(module, "PdfWriter", TrackingWriter)

        merger.merge_to_pdf(
            conversion_rep=report(three_files), output_path=tmp_path / "out.pdf"
        )

        assert closed == [True]


# --------------------------------------------------------------------------
# merge_to_pdf — errors and cancellations
# --------------------------------------------------------------------------
class TestMergeToPdfFailures:
    @pytest.fixture
    def broken(self, tmp_path) -> Path:
        path = tmp_path / "broken.pdf"
        path.write_bytes(b"this is not a pdf")
        return path

    def test_empty_document_list_raises(self, merger, tmp_path):
        out = tmp_path / "out.pdf"

        with pytest.raises(ValueError, match="No valid PDF data to merge"):
            merger.merge_to_pdf(conversion_rep=report([]), output_path=out)

        assert not out.exists()

    def test_broken_file_is_skipped_and_others_merged(self, merger, broken, tmp_path):
        good1 = make_pdf(tmp_path / "g1.pdf", [110])
        good2 = make_pdf(tmp_path / "g2.pdf", [130])
        out = tmp_path / "out.pdf"

        merger.merge_to_pdf(
            conversion_rep=report([item(1, good1), item(2, broken), item(3, good2)]),
            output_path=out,
        )

        assert widths(out) == [110, 130]

    def test_broken_file_reports_warning_with_path(
        self, merger, broken, tmp_path, caplog
    ):
        good = make_pdf(tmp_path / "g.pdf", [110])

        with caplog.at_level(logging.ERROR):
            merger.merge_to_pdf(
                conversion_rep=report([item(1, good), item(2, broken)]),
                output_path=tmp_path / "out.pdf",
            )

        statuses = payloads(merger, "status")
        assert {
            "key": "merging.error.unknown",
            "status": "warning",
            "path": broken,
        } in statuses
        assert "Failed to process broken.pdf" in caplog.text

    def test_missing_file_is_treated_as_failure(self, merger, tmp_path):
        good = make_pdf(tmp_path / "g.pdf", [110])
        missing = tmp_path / "missing.pdf"
        out = tmp_path / "out.pdf"

        merger.merge_to_pdf(
            conversion_rep=report([item(1, good), item(2, missing)]),
            output_path=out,
        )

        assert widths(out) == [110]
        assert payloads(merger, "status")[-1]["failed"] == 1

    def test_progress_is_reported_for_failed_files_too(self, merger, broken, tmp_path):
        good = make_pdf(tmp_path / "g.pdf", [110])

        merger.merge_to_pdf(
            conversion_rep=report([item(1, broken), item(2, good)]),
            output_path=tmp_path / "out.pdf",
        )

        determinate = [
            p for p in payloads(merger, "progress") if p["mode"] == "determinate"
        ]
        assert [p["current"] for p in determinate] == [1, 2]
        assert determinate[0]["filename"] == "broken.pdf"

    def test_done_status_counts_success_and_failed(self, merger, broken, tmp_path):
        good1 = make_pdf(tmp_path / "g1.pdf", [110])
        good2 = make_pdf(tmp_path / "g2.pdf", [120])

        merger.merge_to_pdf(
            conversion_rep=report([item(1, good1), item(2, broken), item(3, good2)]),
            output_path=tmp_path / "out.pdf",
        )

        done = payloads(merger, "status")[-1]
        assert done == {
            "key": "merging.done",
            "status": "info",
            "success": 2,
            "failed": 1,
        }

    def test_failed_count_includes_previous_conversion_failures(
        self, merger, broken, tmp_path
    ):
        good = make_pdf(tmp_path / "g.pdf", [110])

        merger.merge_to_pdf(
            conversion_rep=report([item(1, good), item(2, broken)], failed=2),
            output_path=tmp_path / "out.pdf",
        )

        assert payloads(merger, "status")[-1]["failed"] == 3

    def test_success_ignores_previous_conversion_failures(self, merger, tmp_path):
        files = [
            item(k, make_pdf(tmp_path / f"f{k}.pdf", [100 + k * 10])) for k in (1, 2, 3)
        ]

        merger.merge_to_pdf(
            conversion_rep=report(files, failed=2),
            output_path=tmp_path / "out.pdf",
        )

        done = payloads(merger, "status")[-1]
        assert done["success"] == 3  # all 3 files merged
        assert done["failed"] == 2  # only those that fell before

    def test_all_files_broken_raises_and_writes_nothing(self, merger, broken, tmp_path):
        other = tmp_path / "other.pdf"
        other.write_bytes(b"also not a pdf")
        out = tmp_path / "out.pdf"

        with pytest.raises(ValueError, match="No PDF data"):
            merger.merge_to_pdf(
                conversion_rep=report([item(1, broken), item(2, other)]),
                output_path=out,
            )

        assert not out.exists()

    def test_interruption_propagates_and_writes_nothing(self, merger, tmp_path, caplog):
        files = [
            item(k, make_pdf(tmp_path / f"f{k}.pdf", [100 + k * 10])) for k in (1, 2, 3)
        ]
        out = tmp_path / "out.pdf"
        merger.check_stop.side_effect = [None, InterruptedError()]

        with caplog.at_level(logging.INFO), pytest.raises(InterruptedError):
            merger.merge_to_pdf(conversion_rep=report(files), output_path=out)

        assert not out.exists()
        assert "successfully cancelled" in caplog.text

    def test_interruption_right_before_write_writes_nothing(self, merger, tmp_path):
        files = [item(1, make_pdf(tmp_path / "f1.pdf", [110]))]
        out = tmp_path / "out.pdf"
        # The 1st call is in the loop, the 2nd is before recording
        merger.check_stop.side_effect = [None, InterruptedError()]

        with pytest.raises(InterruptedError):
            merger.merge_to_pdf(conversion_rep=report(files), output_path=out)

        assert not out.exists()

    def test_writer_is_closed_on_cancellation(self, merger, tmp_path, monkeypatch):
        closed = []
        module = sys.modules[PdfMerger.__module__]

        class TrackingWriter(PdfWriter):
            def close(self):
                closed.append(True)
                super().close()

        monkeypatch.setattr(module, "PdfWriter", TrackingWriter)
        files = [item(1, make_pdf(tmp_path / "f1.pdf", [110]))]
        merger.check_stop.side_effect = InterruptedError()

        with pytest.raises(InterruptedError):
            merger.merge_to_pdf(
                conversion_rep=report(files), output_path=tmp_path / "out.pdf"
            )

        assert closed == [True]

    def test_writer_is_closed_on_error(self, merger, broken, tmp_path, monkeypatch):
        closed = []
        module = sys.modules[PdfMerger.__module__]

        class TrackingWriter(PdfWriter):
            def close(self):
                closed.append(True)
                super().close()

        monkeypatch.setattr(module, "PdfWriter", TrackingWriter)

        with pytest.raises(ValueError):
            merger.merge_to_pdf(
                conversion_rep=report([item(1, broken)]),
                output_path=tmp_path / "out.pdf",
            )

        assert closed == [True]
