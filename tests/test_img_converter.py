import logging
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from simple_to_pdf.converters.base_converter import BaseConverter
from simple_to_pdf.converters.img_converter import ImageConverter
from simple_to_pdf.converters.models import ConversionResult


def make_result(success=(), failed=()) -> ConversionResult:
    res = ConversionResult()
    res.success.extend(success)
    res.failed.extend(failed)
    return res


def make_image(path: Path, size=(10, 10), mode="RGB", color="red") -> Path:
    Image.new(mode, size, color).save(path)
    return path


def make_gif(path: Path, colors=("red", "green", "blue")) -> Path:
    frames = [Image.new("RGB", (10, 10), c) for c in colors]
    frames[0].save(path, format="GIF", save_all=True, append_images=frames[1:])
    return path


@pytest.fixture
def converter():
    conv = ImageConverter.__new__(ImageConverter)
    conv.chunk_size = 2
    conv.check_stop = MagicMock()
    return conv


class TestInit:
    def test_sets_supported_formats_and_calls_base_init(self):
        formats = {"image": {".png"}}

        with (
            patch.object(BaseConverter, "__init__", return_value=None) as base_init,
            patch.object(
                ImageConverter,
                "get_supported_formats",
                return_value=formats,
                create=True,
            ),
        ):
            conv = ImageConverter(chunk_size=5)

        base_init.assert_called_once_with(chunk_size=5)
        assert conv.SUPPORTED_FORMATS == formats


class TestConvertToPdf:
    def test_delegates_to_images_conversion(self, converter, tmp_path):
        files = [(0, tmp_path / "a.png")]
        expected = make_result(success=[(0, tmp_path / "a.pdf")])
        converter._convert_images_to_pdf = MagicMock(return_value=expected)

        result = converter.convert_to_pdf(files=files, out_dir=tmp_path)

        converter._convert_images_to_pdf.assert_called_once_with(
            files=files, out_dir=tmp_path
        )
        assert result is expected


class TestConvertImagesToPdf:
    def test_processes_each_chunk_and_aggregates(self, converter, tmp_path):
        chunk1 = [(0, tmp_path / "a.png"), (1, tmp_path / "b.png")]
        chunk2 = [(2, tmp_path / "c.png")]
        converter.make_chunks = MagicMock(return_value=[chunk1, chunk2])
        converter._convert_images_chunk = MagicMock(
            side_effect=[
                make_result(success=[(0, Path("0.pdf"))], failed=[(1, chunk1[1][1])]),
                make_result(success=[(2, Path("2.pdf"))]),
            ]
        )

        result = converter._convert_images_to_pdf(
            files=chunk1 + chunk2, out_dir=tmp_path
        )

        converter.make_chunks.assert_called_once_with(chunk1 + chunk2, 2)
        assert [
            c.kwargs["chunk"] for c in converter._convert_images_chunk.call_args_list
        ] == [
            chunk1,
            chunk2,
        ]
        assert all(
            c.kwargs["out_dir"] == tmp_path
            for c in converter._convert_images_chunk.call_args_list
        )
        assert result.success == [(0, Path("0.pdf")), (2, Path("2.pdf"))]
        assert result.failed == [(1, chunk1[1][1])]

    def test_failed_chunk_is_logged_and_skipped(self, converter, tmp_path, caplog):
        chunk1 = [(0, tmp_path / "a.png")]
        chunk2 = [(1, tmp_path / "b.png")]
        converter.make_chunks = MagicMock(return_value=[chunk1, chunk2])
        converter._convert_images_chunk = MagicMock(
            side_effect=[
                RuntimeError("boom"),
                make_result(success=[(1, Path("1.pdf"))]),
            ]
        )

        with caplog.at_level(logging.ERROR):
            result = converter._convert_images_to_pdf(
                files=chunk1 + chunk2, out_dir=tmp_path
            )

        assert "Chunk conversion error" in caplog.text
        assert result.success == [(1, Path("1.pdf"))]
        assert result.failed == []

    def test_no_files(self, converter, tmp_path):
        converter.make_chunks = MagicMock(return_value=[])

        result = converter._convert_images_to_pdf(files=[], out_dir=tmp_path)

        assert result.success == []
        assert result.failed == []


class TestConvertSingleImage:
    def test_missing_file_returns_none(self, converter, tmp_path):
        assert converter._convert_single_image(tmp_path / "nope.png", tmp_path) is None

    def test_creates_pdf_named_after_stem(self, converter, tmp_path):
        src = make_image(tmp_path / "photo.final.png")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        result = converter._convert_single_image(src, out_dir)

        assert result == out_dir / "photo.final.pdf"
        assert result.read_bytes().startswith(b"%PDF")

    @pytest.mark.parametrize(
        ("mode", "color"),
        [("RGBA", (255, 0, 0, 128)), ("L", 128), ("P", 0)],
    )
    def test_non_rgb_modes_are_converted(self, converter, tmp_path, mode, color):
        src = make_image(tmp_path / "img.png", mode=mode, color=color)

        result = converter._convert_single_image(src, tmp_path)

        assert result is not None
        assert result.read_bytes().startswith(b"%PDF")

    def test_multi_frame_image_gives_multi_page_pdf(self, converter, tmp_path):
        src = make_gif(tmp_path / "anim.gif")
        with Image.open(src) as check:
            assert getattr(check, "n_frames", 1) == 3

        result = converter._convert_single_image(src, tmp_path)

        assert result is not None
        assert re.search(rb"/Count\s+3", result.read_bytes())

    def test_large_image_is_downscaled(self, converter, tmp_path):
        src = make_image(tmp_path / "big.png", size=(3000, 1000))

        with patch.object(
            Image.Image, "thumbnail", autospec=True, side_effect=Image.Image.thumbnail
        ) as thumb:
            result = converter._convert_single_image(src, tmp_path)

        assert result is not None
        thumb.assert_called_once()
        assert thumb.call_args.args[1] == (2500, 2500)

    def test_small_image_is_not_downscaled(self, converter, tmp_path):
        src = make_image(tmp_path / "small.png", size=(100, 100))

        with patch.object(Image.Image, "thumbnail", autospec=True) as thumb:
            result = converter._convert_single_image(src, tmp_path)

        assert result is not None
        thumb.assert_not_called()

    def test_corrupted_file_raises(self, converter, tmp_path):
        src = tmp_path / "broken.png"
        src.write_bytes(b"this is not an image")

        with pytest.raises(OSError):
            converter._convert_single_image(src, tmp_path)

    def test_save_error_propagates_and_leaves_no_pdf(self, converter, tmp_path):
        src = make_image(tmp_path / "a.png")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with (
            patch.object(Image.Image, "save", side_effect=OSError("disk full")),
            pytest.raises(OSError, match="disk full"),
        ):
            converter._convert_single_image(src, out_dir)

        assert list(out_dir.glob("*.pdf")) == []


class TestConvertImagesChunk:
    def test_success(self, converter, tmp_path):
        a, b = tmp_path / "a.png", tmp_path / "b.png"
        converter._convert_single_image = MagicMock(
            side_effect=lambda path, out_dir: out_dir / f"{path.stem}.pdf"
        )

        res = converter._convert_images_chunk(chunk=[(0, a), (1, b)], out_dir=tmp_path)

        assert res.success == [(0, tmp_path / "a.pdf"), (1, tmp_path / "b.pdf")]
        assert res.failed == []
        assert converter.check_stop.call_count == 2
        converter._convert_single_image.assert_any_call(a, tmp_path)
        converter._convert_single_image.assert_any_call(b, tmp_path)

    def test_none_result_is_failed_with_warning(self, converter, tmp_path, caplog):
        a = tmp_path / "a.png"
        converter._convert_single_image = MagicMock(return_value=None)

        with caplog.at_level(logging.WARNING):
            res = converter._convert_images_chunk(chunk=[(3, a)], out_dir=tmp_path)

        assert res.success == []
        assert res.failed == [(3, a)]
        assert "File not found or empty" in caplog.text

    def test_exception_marks_only_that_file_failed(self, converter, tmp_path, caplog):
        a, b = tmp_path / "a.png", tmp_path / "b.png"

        def flaky(path, out_dir):
            if path == a:
                raise OSError("cannot identify image")
            return out_dir / f"{path.stem}.pdf"

        converter._convert_single_image = MagicMock(side_effect=flaky)

        with caplog.at_level(logging.ERROR):
            res = converter._convert_images_chunk(
                chunk=[(0, a), (1, b)], out_dir=tmp_path
            )

        assert res.failed == [(0, a)]
        assert res.success == [(1, tmp_path / "b.pdf")]
        assert "Error converting a.png" in caplog.text

    def test_stop_signal_propagates(self, converter, tmp_path):
        converter.check_stop = MagicMock(side_effect=InterruptedError)
        converter._convert_single_image = MagicMock()

        with pytest.raises(InterruptedError):
            converter._convert_images_chunk(
                chunk=[(0, tmp_path / "a.png")], out_dir=tmp_path
            )

        converter._convert_single_image.assert_not_called()

    def test_real_conversion_end_to_end(self, converter, tmp_path):
        good = make_image(tmp_path / "good.png")
        missing = tmp_path / "missing.png"
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        res = converter._convert_images_chunk(
            chunk=[(0, good), (1, missing)], out_dir=out_dir
        )

        assert res.success == [(0, out_dir / "good.pdf")]
        assert res.failed == [(1, missing)]
        assert (out_dir / "good.pdf").read_bytes().startswith(b"%PDF")
