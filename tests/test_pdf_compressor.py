# pyright: reportAttributeAccessIssue=false
import io
import logging
import random
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pymupdf
import pytest
from PIL import Image

from simple_to_pdf.pdf.pdf_compressor import PDFCompressor


def noisy_png(seed: int = 0, size: int = 200) -> bytes:
    """PNGwith random noise: PNG is large and JPEG q=20 is noticeably smaller."""
    raw = random.Random(seed).randbytes(size * size * 3)
    buffer = io.BytesIO()
    Image.frombytes("RGB", (size, size), raw).save(buffer, format="PNG")
    return buffer.getvalue()


def make_pdf(path: Path, *, pages: int = 2, with_images: bool = True) -> Path:
    """Creates a real PDF; each page has its own noisy picture."""
    doc = pymupdf.open()
    for n in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {n + 1}")
        if with_images:
            page.insert_image(pymupdf.Rect(50, 100, 250, 300), stream=noisy_png(seed=n))
    doc.save(path)
    doc.close()
    return path


def fake_document(monkeypatch, *, pages: int = 1) -> MagicMock:
    """Replaces pymupdf.open with a fake document."""
    doc = MagicMock()
    doc.__len__.return_value = pages
    doc.__getitem__.side_effect = lambda i: MagicMock(name=f"page{i}")
    doc.__enter__.return_value = doc
    monkeypatch.setattr(pymupdf, "open", MagicMock(return_value=doc))
    return doc


ERROR_STATUS = {"key": "compressing.error.critical", "status": "error"}


def payloads(compressor: PDFCompressor, kind: str) -> list[dict]:
    """All dictionaries passed to _show_callback with this message type."""
    return [
        c.args[1] for c in compressor._show_callback.call_args_list if c.args[0] == kind
    ]


@pytest.fixture
def compressor() -> PDFCompressor:
    comp = PDFCompressor()
    comp._show_callback = MagicMock()
    comp.check_stop = MagicMock()
    return comp


@pytest.fixture
def rgb_info():
    """Fake PixInfo: 16x16 RGB with noise."""
    return SimpleNamespace(
        samples=random.Random(1).randbytes(16 * 16 * 3), width=16, height=16
    )


class TestInit:
    def test_defaults(self):
        comp = PDFCompressor()

        assert comp.garbage_level == 4
        assert comp.deflate is True
        assert comp.clean is True

    def test_custom_values(self):
        comp = PDFCompressor(garbage_level=1, deflate=False, clean=False)

        assert comp.garbage_level == 1
        assert comp.deflate is False
        assert comp.clean is False


class TestGetPixInfo:
    WIDTH, HEIGHT = 4, 2

    def _pixmap(self, colorspace, alpha: bool) -> pymupdf.Pixmap:
        pix = pymupdf.Pixmap(
            colorspace, pymupdf.IRect(0, 0, self.WIDTH, self.HEIGHT), alpha
        )
        pix.clear_with(200)
        return pix

    def test_no_colorspace_returns_none(self, compressor):
        pix = MagicMock()
        pix.colorspace = None

        assert compressor._get_pix_info(pix) is None

    def test_rgb_without_alpha_used_as_is(self, compressor):
        pix = self._pixmap(pymupdf.csRGB, alpha=False)

        info = compressor._get_pix_info(pix)

        assert (info.width, info.height) == (self.WIDTH, self.HEIGHT)
        assert info.samples == pix.samples

    def test_grayscale_converted_to_rgb(self, compressor):
        pix = self._pixmap(pymupdf.csGRAY, alpha=False)
        assert pix.n == 1

        info = compressor._get_pix_info(pix)

        assert (info.width, info.height) == (self.WIDTH, self.HEIGHT)
        assert len(info.samples) == self.WIDTH * self.HEIGHT * 3

    def test_rgba_converted_to_rgb_without_alpha(self, compressor):
        pix = self._pixmap(pymupdf.csRGB, alpha=True)
        assert pix.n == 4

        info = compressor._get_pix_info(pix)

        assert len(info.samples) == self.WIDTH * self.HEIGHT * 3

    def test_conversion_error_is_logged_and_reraised(
        self, compressor, monkeypatch, caplog
    ):
        pix = MagicMock()
        pix.n = 1
        pix.alpha = 0
        monkeypatch.setattr(
            pymupdf, "Pixmap", MagicMock(side_effect=RuntimeError("boom"))
        )

        with (
            caplog.at_level(logging.WARNING),
            pytest.raises(RuntimeError, match="boom"),
        ):
            compressor._get_pix_info(pix)

        assert "Could not convert pixmap" in caplog.text


class TestCompressSingleImage:
    @pytest.fixture
    def page(self):
        return MagicMock()

    @pytest.fixture
    def doc(self):
        return MagicMock()

    @pytest.fixture
    def pixmap_factory(self, monkeypatch):
        def _install(colorspace_name: str = "DeviceRGB") -> MagicMock:
            pix = MagicMock()
            pix.colorspace.name = colorspace_name
            monkeypatch.setattr(pymupdf, "Pixmap", MagicMock(return_value=pix))
            return pix

        return _install

    def test_replaces_image_when_jpeg_is_smaller(
        self, compressor, page, doc, pixmap_factory, rgb_info
    ):
        doc.extract_image.return_value = {"image": b"x" * 100_000}
        pixmap_factory()
        compressor._get_pix_info = MagicMock(return_value=rgb_info)

        compressor._compress_single_image(page=page, doc=doc, xref=7, quality=20)

        page.replace_image.assert_called_once()
        args, kwargs = page.replace_image.call_args
        assert args == (7,)
        assert kwargs["stream"][:2] == b"\xff\xd8"
        assert len(kwargs["stream"]) < 100_000

    def test_keeps_original_when_jpeg_is_larger(
        self, compressor, page, doc, pixmap_factory, rgb_info
    ):
        doc.extract_image.return_value = {"image": b"x"}
        pixmap_factory()
        compressor._get_pix_info = MagicMock(return_value=rgb_info)

        compressor._compress_single_image(page=page, doc=doc, xref=7, quality=20)

        page.replace_image.assert_not_called()

    def test_quality_affects_output_size(
        self, compressor, page, doc, pixmap_factory, rgb_info
    ):
        doc.extract_image.return_value = {"image": b"x" * 1_000_000}
        pixmap_factory()
        compressor._get_pix_info = MagicMock(return_value=rgb_info)

        compressor._compress_single_image(page=page, doc=doc, xref=1, quality=10)
        compressor._compress_single_image(page=page, doc=doc, xref=1, quality=95)

        low, high = (c.kwargs["stream"] for c in page.replace_image.call_args_list)
        assert len(low) < len(high)

    @pytest.mark.parametrize("img_info", [None, {}])
    def test_no_image_info_is_skipped(
        self, compressor, page, doc, monkeypatch, img_info
    ):
        doc.extract_image.return_value = img_info
        pixmap_cls = MagicMock()
        monkeypatch.setattr(pymupdf, "Pixmap", pixmap_cls)

        compressor._compress_single_image(page=page, doc=doc, xref=7, quality=20)

        pixmap_cls.assert_not_called()
        page.replace_image.assert_not_called()

    @pytest.mark.parametrize("colorspace", ["DeviceCMYK", "Indexed"])
    def test_unsupported_colorspaces_are_skipped(
        self, compressor, page, doc, pixmap_factory, colorspace
    ):
        doc.extract_image.return_value = {"image": b"x" * 100_000}
        pixmap_factory(colorspace)
        compressor._get_pix_info = MagicMock()

        compressor._compress_single_image(page=page, doc=doc, xref=7, quality=20)

        compressor._get_pix_info.assert_not_called()
        page.replace_image.assert_not_called()

    def test_pix_info_none_is_skipped(self, compressor, page, doc, pixmap_factory):
        doc.extract_image.return_value = {"image": b"x" * 100_000}
        pixmap_factory()
        compressor._get_pix_info = MagicMock(return_value=None)

        compressor._compress_single_image(page=page, doc=doc, xref=7, quality=20)

        page.replace_image.assert_not_called()

    def test_exception_is_logged_and_not_raised(self, compressor, page, doc, caplog):
        doc.extract_image.side_effect = RuntimeError("broken image")

        with caplog.at_level(logging.ERROR):
            compressor._compress_single_image(page=page, doc=doc, xref=42, quality=20)

        assert "Image compressing failed 42" in caplog.text
        page.replace_image.assert_not_called()

    def test_replace_image_error_is_swallowed(
        self, compressor, page, doc, pixmap_factory, rgb_info, caplog
    ):
        doc.extract_image.return_value = {"image": b"x" * 100_000}
        pixmap_factory()
        compressor._get_pix_info = MagicMock(return_value=rgb_info)
        page.replace_image.side_effect = RuntimeError("cannot replace")

        with caplog.at_level(logging.ERROR):
            compressor._compress_single_image(page=page, doc=doc, xref=5, quality=20)

        assert "Image compressing failed 5" in caplog.text


class TestSetPageImagesQuality:
    @pytest.fixture
    def spy(self, compressor):
        compressor._compress_single_image = MagicMock()
        return compressor._compress_single_image

    def test_compresses_every_image(self, compressor, spy):
        page = MagicMock()
        page.get_images.return_value = [(10,), (11,)]
        doc = MagicMock()
        processed: set[int] = set()

        compressor._set_page_images_quality(
            page, doc=doc, quality=33, processed_xrefs=processed
        )

        xrefs = [c.kwargs["xref"] for c in spy.call_args_list]
        assert xrefs == [10, 11]
        assert all(c.kwargs["quality"] == 33 for c in spy.call_args_list)
        assert all(c.kwargs["page"] is page for c in spy.call_args_list)
        assert all(c.kwargs["doc"] is doc for c in spy.call_args_list)
        assert processed == {10, 11}

    def test_duplicate_xref_on_page_compressed_once(self, compressor, spy):
        page = MagicMock()
        page.get_images.return_value = [(10,), (10,), (11,)]

        compressor._set_page_images_quality(
            page, doc=MagicMock(), quality=20, processed_xrefs=set()
        )

        assert [c.kwargs["xref"] for c in spy.call_args_list] == [10, 11]

    def test_already_processed_xrefs_are_skipped(self, compressor, spy):
        page = MagicMock()
        page.get_images.return_value = [(10,), (11,)]

        compressor._set_page_images_quality(
            page, doc=MagicMock(), quality=20, processed_xrefs={10}
        )

        assert [c.kwargs["xref"] for c in spy.call_args_list] == [11]

    def test_shared_state_across_pages(self, compressor, spy):
        processed: set[int] = set()
        page1, page2 = MagicMock(), MagicMock()
        page1.get_images.return_value = [(10,)]
        page2.get_images.return_value = [(10,), (12,)]

        for page in (page1, page2):
            compressor._set_page_images_quality(
                page, doc=MagicMock(), quality=20, processed_xrefs=processed
            )

        assert [c.kwargs["xref"] for c in spy.call_args_list] == [10, 12]

    def test_get_images_error_is_logged_and_ignored(self, compressor, spy, caplog):
        page = MagicMock()
        page.get_images.side_effect = RuntimeError("bad page")

        with caplog.at_level(logging.ERROR):
            compressor._set_page_images_quality(
                page, doc=MagicMock(), quality=20, processed_xrefs=set()
            )

        assert "page.get_image error!" in caplog.text
        spy.assert_not_called()

    def test_check_stop_called_per_image(self, compressor, spy):
        page = MagicMock()
        page.get_images.return_value = [(1,), (2,), (3,)]

        compressor._set_page_images_quality(
            page, doc=MagicMock(), quality=20, processed_xrefs=set()
        )

        assert compressor.check_stop.call_count == 3

    def test_interruption_propagates(self, compressor, spy):
        page = MagicMock()
        page.get_images.return_value = [(1,), (2,)]
        compressor.check_stop.side_effect = InterruptedError()

        with pytest.raises(InterruptedError):
            compressor._set_page_images_quality(
                page, doc=MagicMock(), quality=20, processed_xrefs=set()
            )

        spy.assert_not_called()


class TestIsHardPage:
    def test_many_drawings_is_hard(self, compressor):
        page = MagicMock()
        page.get_drawings.return_value = [None] * 1001

        assert compressor.is_hard_page(page=page) is True

    def test_threshold_is_exclusive(self, compressor):
        page = MagicMock()
        page.get_drawings.return_value = [None] * 1000

        assert compressor.is_hard_page(page=page) is False

    def test_no_drawings_is_not_hard(self, compressor):
        page = MagicMock()
        page.get_drawings.return_value = []

        assert compressor.is_hard_page(page=page) is False

    def test_error_returns_false_and_logs(self, compressor, caplog):
        page = MagicMock()
        page.get_drawings.side_effect = RuntimeError("parse error")

        with caplog.at_level(logging.ERROR):
            assert compressor.is_hard_page(page=page) is False

        assert "Page parsing error!" in caplog.text

    def test_page_must_be_passed_by_keyword(self, compressor):
        with pytest.raises(TypeError):
            compressor.is_hard_page(MagicMock())


class TestCompressIntegration:
    def test_reduces_file_size(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf", pages=2)
        out = tmp_path / "out.pdf"

        result = compressor.compress(input_pdf_path=src, quality=20, output_path=out)

        assert result == out
        assert out.exists()
        assert out.stat().st_size < src.stat().st_size

    def test_page_count_preserved(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf", pages=3)
        out = tmp_path / "out.pdf"

        compressor.compress(input_pdf_path=src, output_path=out)

        with pymupdf.open(out) as doc:
            assert len(doc) == 3

    def test_images_become_jpeg(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf", pages=1)
        out = tmp_path / "out.pdf"

        compressor.compress(input_pdf_path=src, quality=20, output_path=out)

        with pymupdf.open(src) as before, pymupdf.open(out) as after:
            xref_before = before[0].get_images(full=True)[0][0]
            xref_after = after[0].get_images(full=True)[0][0]
            assert before.extract_image(xref_before)["ext"] == "png"
            assert after.extract_image(xref_after)["ext"] == "jpeg"

    def test_lower_quality_gives_smaller_file(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf", pages=1)
        low = tmp_path / "low.pdf"
        high = tmp_path / "high.pdf"

        compressor.compress(input_pdf_path=src, quality=5, output_path=low)
        compressor.compress(input_pdf_path=src, quality=90, output_path=high)

        assert low.stat().st_size < high.stat().st_size

    def test_pdf_without_images(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf", pages=2, with_images=False)
        out = tmp_path / "out.pdf"

        result = compressor.compress(input_pdf_path=src, output_path=out)

        assert result == out
        with pymupdf.open(out) as doc:
            assert len(doc) == 2

    def test_original_file_is_not_modified(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf")
        before = src.read_bytes()

        compressor.compress(input_pdf_path=src, output_path=tmp_path / "out.pdf")

        assert src.read_bytes() == before

    def test_progress_and_status_callbacks(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf", pages=3)

        compressor.compress(input_pdf_path=src, output_path=tmp_path / "out.pdf")

        progress = payloads(compressor, "progress")
        assert progress[0] == {"stage": "compressing", "mode": "indeterminate"}
        assert progress[1:4] == [
            {"stage": "compressing", "mode": "determinate", "current": i, "total": 3}
            for i in (1, 2, 3)
        ]
        assert progress[4] == {"stage": "processing", "mode": "indeterminate"}
        assert len(progress) == 5

        assert payloads(compressor, "status") == [
            {"key": "compressing.done", "status": "info"}
        ]

    def test_all_callbacks_are_forced(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf", pages=1)

        compressor.compress(input_pdf_path=src, output_path=tmp_path / "out.pdf")

        assert compressor._show_callback.call_args_list
        assert all(
            c.kwargs.get("force") is True
            for c in compressor._show_callback.call_args_list
        )

    def test_interruption_propagates_and_no_output(self, compressor, tmp_path):
        src = make_pdf(tmp_path / "in.pdf")
        out = tmp_path / "out.pdf"
        compressor.check_stop.side_effect = InterruptedError()

        with pytest.raises(InterruptedError):
            compressor.compress(input_pdf_path=src, output_path=out)

        assert not out.exists()
        assert payloads(compressor, "status") == []

    def test_interruption_is_logged(self, compressor, tmp_path, caplog):
        src = make_pdf(tmp_path / "in.pdf")
        compressor.check_stop.side_effect = InterruptedError()

        with caplog.at_level(logging.INFO), pytest.raises(InterruptedError):
            compressor.compress(input_pdf_path=src, output_path=tmp_path / "out.pdf")

        assert "interrupted by user" in caplog.text


class TestCompressFailures:
    """In case of any error, compress returns the input path and sends an error status."""

    def test_missing_input_returns_input_path(self, compressor, tmp_path):
        src = tmp_path / "missing.pdf"

        result = compressor.compress(
            input_pdf_path=src, output_path=tmp_path / "out.pdf"
        )

        assert result == src
        assert payloads(compressor, "status") == [ERROR_STATUS]

    def test_corrupted_pdf_returns_input_path(self, compressor, tmp_path):
        src = tmp_path / "broken.pdf"
        src.write_bytes(b"this is definitely not a pdf")
        out = tmp_path / "out.pdf"

        result = compressor.compress(input_pdf_path=src, output_path=out)

        assert result == src
        assert not out.exists()
        assert payloads(compressor, "status") == [ERROR_STATUS]

    def test_pdf_without_pages_returns_input_path(
        self, compressor, tmp_path, monkeypatch, caplog
    ):
        src = tmp_path / "empty.pdf"
        fake_document(monkeypatch, pages=0)

        with caplog.at_level(logging.ERROR):
            result = compressor.compress(
                input_pdf_path=src, output_path=tmp_path / "out.pdf"
            )

        assert result == src
        assert "contains no pages" in caplog.text
        assert payloads(compressor, "status") == [ERROR_STATUS]

    def test_save_error_returns_input_path(self, compressor, tmp_path, monkeypatch):
        src = tmp_path / "in.pdf"
        doc = fake_document(monkeypatch, pages=1)
        compressor._set_page_images_quality = MagicMock()
        doc.save.side_effect = RuntimeError("disk full")

        result = compressor.compress(
            input_pdf_path=src, output_path=tmp_path / "out.pdf"
        )

        assert result == src
        assert payloads(compressor, "status") == [ERROR_STATUS]

    def test_output_equal_to_input_is_not_supported(self, compressor, tmp_path):
        """pymupdf не дозволяє зберігати поверх оригіналу без incremental."""
        src = make_pdf(tmp_path / "in.pdf")

        result = compressor.compress(input_pdf_path=src, output_path=src)

        assert result == src
        assert payloads(compressor, "status") == [ERROR_STATUS]


class TestCompressOrchestration:
    def test_save_called_with_configured_options(self, tmp_path, monkeypatch):
        comp = PDFCompressor(garbage_level=2, deflate=False, clean=False)
        comp._show_callback = MagicMock()
        comp.check_stop = MagicMock()
        comp._set_page_images_quality = MagicMock()
        doc = fake_document(monkeypatch, pages=1)
        out = tmp_path / "out.pdf"

        result = comp.compress(input_pdf_path=tmp_path / "in.pdf", output_path=out)

        doc.save.assert_called_once_with(out, garbage=2, deflate=False, clean=False)
        assert result == out

    def test_quality_is_forwarded_to_pages(self, compressor, tmp_path, monkeypatch):
        compressor._set_page_images_quality = MagicMock()
        fake_document(monkeypatch, pages=2)

        compressor.compress(
            input_pdf_path=tmp_path / "in.pdf",
            quality=55,
            output_path=tmp_path / "out.pdf",
        )

        calls = compressor._set_page_images_quality.call_args_list
        assert len(calls) == 2
        assert all(c.kwargs["quality"] == 55 for c in calls)

    def test_xrefs_set_shared_between_pages(self, compressor, tmp_path, monkeypatch):
        compressor._set_page_images_quality = MagicMock()
        fake_document(monkeypatch, pages=3)

        compressor.compress(
            input_pdf_path=tmp_path / "in.pdf", output_path=tmp_path / "out.pdf"
        )

        sets = [
            c.kwargs["processed_xrefs"]
            for c in compressor._set_page_images_quality.call_args_list
        ]
        assert len(sets) == 3
        assert sets[0] is sets[1] is sets[2]

    def test_hard_pages_are_skipped_but_file_is_saved(
        self, compressor, tmp_path, monkeypatch
    ):
        compressor._set_page_images_quality = MagicMock()
        compressor.is_hard_page = MagicMock(side_effect=[True, False, True])
        doc = fake_document(monkeypatch, pages=3)

        compressor.compress(
            input_pdf_path=tmp_path / "in.pdf", output_path=tmp_path / "out.pdf"
        )

        assert compressor._set_page_images_quality.call_count == 1
        doc.save.assert_called_once()

    def test_check_stop_called_for_every_page(self, compressor, tmp_path, monkeypatch):
        compressor._set_page_images_quality = MagicMock()
        fake_document(monkeypatch, pages=4)

        compressor.compress(
            input_pdf_path=tmp_path / "in.pdf", output_path=tmp_path / "out.pdf"
        )

        assert compressor.check_stop.call_count == 4

    def test_default_quality_is_20(self, compressor, tmp_path, monkeypatch):
        compressor._set_page_images_quality = MagicMock()
        fake_document(monkeypatch, pages=1)

        compressor.compress(
            input_pdf_path=tmp_path / "in.pdf", output_path=tmp_path / "out.pdf"
        )

        assert compressor._set_page_images_quality.call_args.kwargs["quality"] == 20
