import importlib
import logging
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from simple_to_pdf.converters.img_converter import ImageConverter
from simple_to_pdf.converters.models import ConversionResult


def _install_win32_stubs() -> None:
    try:
        importlib.import_module("pythoncom")
        importlib.import_module("win32com.client")
        return
    except ImportError:
        pass
    client = MagicMock()
    package = MagicMock()
    package.client = client
    sys.modules["pythoncom"] = MagicMock()
    sys.modules["win32com"] = package
    sys.modules["win32com.client"] = client


_install_win32_stubs()

mod = importlib.import_module("simple_to_pdf.converters.ms_office_converter")
MSOfficeConverter = mod.MSOfficeConverter
OfficeApp = mod.OfficeApp


def make_result(success=(), failed=()) -> ConversionResult:
    res = ConversionResult()
    res.success.extend(success)
    res.failed.extend(failed)
    return res


def touch(path: Path, content: bytes = b"x") -> Path:
    path.write_bytes(content)
    return path


@pytest.fixture
def converter():
    conv = MSOfficeConverter.__new__(MSOfficeConverter)
    conv.chunk_size = 2
    conv.check_stop = MagicMock()
    return conv


@pytest.fixture
def routing_converter(converter):
    converter.is_table_file = lambda *, file_path: file_path.suffix == ".xlsx"
    converter.is_document_file = lambda *, file_path: file_path.suffix == ".docx"
    converter.is_presentation_file = lambda *, file_path: file_path.suffix == ".pptx"
    converter.is_image_file = lambda *, file_path: file_path.suffix == ".png"
    return converter


class TestOfficeApp:
    def test_prog_ids(self):
        assert OfficeApp.WORD == "Word.Application"
        assert OfficeApp.EXCEL == "Excel.Application"
        assert OfficeApp.POWERPOINT == "PowerPoint.Application"


class TestInit:
    def test_sets_supported_formats_and_calls_base_init(self):
        formats = {"table": {".xlsx"}, "document": {".docx"}, "presentation": {".pptx"}}

        with (
            patch.object(ImageConverter, "__init__", return_value=None) as base_init,
            patch.object(
                MSOfficeConverter,
                "get_supported_formats",
                return_value=formats,
                create=True,
            ),
        ):
            conv = MSOfficeConverter(chunk_size=7)

        base_init.assert_called_once_with(chunk_size=7)
        assert conv.SUPPORTED_FORMATS == formats


class TestConvertToPdf:
    def test_routes_files_by_category_and_aggregates(self, routing_converter, tmp_path):
        xlsx = touch(tmp_path / "a.xlsx")
        docx = touch(tmp_path / "b.docx")
        pptx = touch(tmp_path / "c.pptx")
        png = touch(tmp_path / "d.png")
        unknown = touch(tmp_path / "e.bin")
        missing = tmp_path / "missing.docx"

        def fake_convert(*, files, app_type, out_dir):
            return make_result(success=[(i, tmp_path / f"{i}.pdf") for i, _ in files])

        routing_converter._convert_files_to_pdf = MagicMock(side_effect=fake_convert)
        routing_converter._convert_images_to_pdf = MagicMock(
            return_value=make_result(
                success=[(3, tmp_path / "3.pdf")], failed=[(9, png)]
            )
        )

        result = routing_converter.convert_to_pdf(
            files=[
                (0, xlsx),
                (1, docx),
                (2, pptx),
                (3, png),
                (4, unknown),
                (5, missing),
            ],
            out_dir=tmp_path,
        )

        calls = routing_converter._convert_files_to_pdf.call_args_list
        assert [c.kwargs["app_type"] for c in calls] == [
            OfficeApp.EXCEL,
            OfficeApp.WORD,
            OfficeApp.POWERPOINT,
        ]
        assert [c.kwargs["files"] for c in calls] == [
            [(0, xlsx)],
            [(1, docx)],
            [(2, pptx)],
        ]
        assert all(c.kwargs["out_dir"] == tmp_path for c in calls)
        routing_converter._convert_images_to_pdf.assert_called_once_with(
            files=[(3, png)], out_dir=tmp_path
        )
        assert [i for i, _ in result.success] == [0, 1, 2, 3]
        assert result.failed == [(9, png)]

    def test_only_needed_converters_are_called(self, routing_converter, tmp_path):
        docx = touch(tmp_path / "b.docx")
        routing_converter._convert_files_to_pdf = MagicMock(
            return_value=make_result(success=[(1, tmp_path / "1.pdf")])
        )
        routing_converter._convert_images_to_pdf = MagicMock()

        result = routing_converter.convert_to_pdf(files=[(1, docx)], out_dir=tmp_path)

        routing_converter._convert_files_to_pdf.assert_called_once_with(
            files=[(1, docx)], app_type=OfficeApp.WORD, out_dir=tmp_path
        )
        routing_converter._convert_images_to_pdf.assert_not_called()
        assert result.success == [(1, tmp_path / "1.pdf")]

    def test_nothing_to_convert(self, routing_converter, tmp_path):
        routing_converter._convert_files_to_pdf = MagicMock()
        routing_converter._convert_images_to_pdf = MagicMock()

        result = routing_converter.convert_to_pdf(
            files=[(0, tmp_path / "missing.docx"), (1, touch(tmp_path / "x.bin"))],
            out_dir=tmp_path,
        )

        routing_converter._convert_files_to_pdf.assert_not_called()
        routing_converter._convert_images_to_pdf.assert_not_called()
        assert result.success == []
        assert result.failed == []


class TestConvertFilesToPdf:
    def test_empty_files_returns_empty_result(self, converter, tmp_path):
        converter.make_chunks = MagicMock()
        converter._process_chunk = MagicMock()

        result = converter._convert_files_to_pdf(
            files=[], app_type=OfficeApp.WORD, out_dir=tmp_path
        )

        converter.make_chunks.assert_not_called()
        converter._process_chunk.assert_not_called()
        assert result.success == []
        assert result.failed == []

    def test_processes_each_chunk_and_aggregates(self, converter, tmp_path):
        chunk1 = [(0, tmp_path / "a.docx"), (1, tmp_path / "b.docx")]
        chunk2 = [(2, tmp_path / "c.docx")]
        converter.make_chunks = MagicMock(return_value=[chunk1, chunk2])
        converter._process_chunk = MagicMock(
            side_effect=[
                make_result(success=[(0, Path("0.pdf"))], failed=[(1, chunk1[1][1])]),
                make_result(success=[(2, Path("2.pdf"))]),
            ]
        )

        result = converter._convert_files_to_pdf(
            files=chunk1 + chunk2, app_type=OfficeApp.WORD, out_dir=tmp_path
        )

        converter.make_chunks.assert_called_once_with(chunk1 + chunk2, n=2)
        assert [c.kwargs["chunk"] for c in converter._process_chunk.call_args_list] == [
            chunk1,
            chunk2,
        ]
        assert all(
            c.kwargs["app_type"] == OfficeApp.WORD and c.kwargs["out_dir"] == tmp_path
            for c in converter._process_chunk.call_args_list
        )
        assert result.success == [(0, Path("0.pdf")), (2, Path("2.pdf"))]
        assert result.failed == [(1, chunk1[1][1])]


class TestGetAppInstance:
    def test_returns_dispatched_app(self, converter):
        app = MagicMock()
        with patch.object(mod, "win32") as w32:
            w32.DispatchEx.return_value = app
            converter._clear_cache = MagicMock()

            result = converter._get_app_instance(app_type=OfficeApp.EXCEL)

        assert result is app
        w32.DispatchEx.assert_called_once_with(OfficeApp.EXCEL)
        converter._clear_cache.assert_not_called()

    def test_retries_after_cache_cleanup(self, converter):
        app = MagicMock()
        with patch.object(mod, "win32") as w32:
            w32.DispatchEx.side_effect = [RuntimeError("bad cache"), app]
            converter._clear_cache = MagicMock()

            result = converter._get_app_instance(app_type=OfficeApp.WORD)

        assert result is app
        assert w32.DispatchEx.call_count == 2
        converter._clear_cache.assert_called_once()

    def test_returns_none_if_retry_fails(self, converter):
        with patch.object(mod, "win32") as w32:
            w32.DispatchEx.side_effect = [RuntimeError("one"), RuntimeError("two")]
            converter._clear_cache = MagicMock()

            result = converter._get_app_instance(app_type=OfficeApp.WORD)

        assert result is None
        assert w32.DispatchEx.call_count == 2
        converter._clear_cache.assert_called_once()


class TestClearCache:
    def test_removes_gen_py_modules_and_cache_dir(self, converter, tmp_path):
        cache_dir = tmp_path / "gen_py"
        cache_dir.mkdir()
        touch(cache_dir / "module.py")
        fake_modules = {
            "win32com.gen_py": MagicMock(),
            "win32com.gen_py.abc": MagicMock(),
            "unrelated_test_module": MagicMock(),
        }

        with (
            patch.dict(sys.modules, fake_modules),
            patch.object(mod, "gencache") as cache,
        ):
            cache.GetGeneratePath.return_value = str(cache_dir)

            converter._clear_cache()

            assert "win32com.gen_py" not in sys.modules
            assert "win32com.gen_py.abc" not in sys.modules
            assert "unrelated_test_module" in sys.modules

        assert not cache_dir.exists()

    def test_missing_cache_dir_is_ok(self, converter, tmp_path):
        with patch.object(mod, "gencache") as cache:
            cache.GetGeneratePath.return_value = str(tmp_path / "nope")

            converter._clear_cache()

    def test_errors_are_logged_not_raised(self, converter, caplog):
        with patch.object(mod, "gencache") as cache, caplog.at_level(logging.WARNING):
            cache.GetGeneratePath.side_effect = OSError("denied")

            converter._clear_cache()

        assert "Failed to clear cache" in caplog.text


class TestGetProcessor:
    @pytest.mark.parametrize(
        ("app_type", "method_name"),
        [
            (OfficeApp.WORD, "_convert_doc_to_pdf"),
            (OfficeApp.EXCEL, "_convert_table_to_pdf"),
            (OfficeApp.POWERPOINT, "_convert_pres_to_pdf"),
        ],
    )
    def test_returns_matching_processor(self, converter, app_type, method_name):
        assert converter._get_processor(app_type=app_type) == getattr(
            converter, method_name
        )


class TestDisableVisibility:
    def test_excel_hides_window_and_alerts(self, converter):
        app = SimpleNamespace(Visible=True, DisplayAlerts=True)

        converter._disable_visibility(app=app, app_type=OfficeApp.EXCEL)

        assert app.Visible is False
        assert app.DisplayAlerts is False

    def test_word_uses_zero_for_alerts(self, converter):
        app = SimpleNamespace(Visible=True, DisplayAlerts=-1)

        converter._disable_visibility(app=app, app_type=OfficeApp.WORD)

        assert app.Visible is False
        assert app.DisplayAlerts == 0

    def test_powerpoint_does_not_touch_visible(self, converter):
        app = SimpleNamespace(Visible=True, DisplayAlerts=True)

        converter._disable_visibility(app=app, app_type=OfficeApp.POWERPOINT)

        assert app.Visible is True
        assert app.DisplayAlerts is False

    def test_missing_attributes_are_skipped(self, converter):
        app = SimpleNamespace()

        converter._disable_visibility(app=app, app_type=OfficeApp.EXCEL)

        assert not hasattr(app, "Visible")
        assert not hasattr(app, "DisplayAlerts")

    def test_unknown_config_logs_warning(self, converter, caplog):
        converter.OFFICE_CONFIG = {}
        app = SimpleNamespace(Visible=True, DisplayAlerts=True)

        with caplog.at_level(logging.WARNING):
            converter._disable_visibility(app=app, app_type=OfficeApp.EXCEL)

        assert "No configuration found" in caplog.text
        assert app.Visible is True
        assert app.DisplayAlerts is True

    def test_setter_errors_are_logged_and_do_not_stop_configuration(
        self, converter, caplog
    ):
        class StubbornApp:
            DisplayAlerts = True

            @property
            def Visible(self):
                return True

            @Visible.setter
            def Visible(self, value):
                raise RuntimeError("read-only")

        app = StubbornApp()

        with caplog.at_level(logging.WARNING):
            converter._disable_visibility(app=app, app_type=OfficeApp.EXCEL)

        assert "Could not set Visible" in caplog.text
        assert app.DisplayAlerts is False


class TestConvertChunkFiles:
    @pytest.fixture
    def env(self, converter):
        converter._prepare_temp_files = MagicMock(
            side_effect=lambda *, chunk, tmp_dir: [
                tmp_dir / f"tmp_{p.name}" for _, p in chunk
            ]
        )
        processor = MagicMock(
            side_effect=lambda *, app, file_path, output_path: output_path
        )
        converter._get_processor = MagicMock(return_value=processor)
        return converter, processor

    def test_success(self, env, tmp_path):
        converter, processor = env
        out_dir = tmp_path / "out"
        tmp_dir = tmp_path / "tmp"
        chunk = [(0, tmp_path / "a.docx"), (1, tmp_path / "b.docx")]
        chunk_res = ConversionResult()
        app = MagicMock()

        with patch.object(mod, "get_unique_path", side_effect=lambda p: p):
            converter._convert_chunk_files(
                app=app,
                app_type=OfficeApp.WORD,
                chunk=chunk,
                tmp_dir=tmp_dir,
                out_dir=out_dir,
                chunk_res=chunk_res,
            )

        assert chunk_res.success == [(0, out_dir / "a.pdf"), (1, out_dir / "b.pdf")]
        assert chunk_res.failed == []
        assert converter.check_stop.call_count == 2
        converter._get_processor.assert_called_with(app_type=OfficeApp.WORD)
        first_call = processor.call_args_list[0].kwargs
        assert first_call["app"] is app
        assert first_call["file_path"] == tmp_dir / "tmp_a.docx"
        assert first_call["output_path"] == out_dir / "a.pdf"

    def test_failure_of_one_file_does_not_stop_others(self, env, tmp_path):
        converter, processor = env
        out_dir = tmp_path / "out"
        chunk = [(0, tmp_path / "a.docx"), (1, tmp_path / "b.docx")]
        chunk_res = ConversionResult()

        def flaky(*, app, file_path, output_path):
            if file_path.name == "tmp_a.docx":
                raise ValueError("corrupted")
            return output_path

        processor.side_effect = flaky

        with patch.object(mod, "get_unique_path", side_effect=lambda p: p):
            converter._convert_chunk_files(
                app=MagicMock(),
                app_type=OfficeApp.WORD,
                chunk=chunk,
                tmp_dir=tmp_path / "tmp",
                out_dir=out_dir,
                chunk_res=chunk_res,
            )

        assert chunk_res.failed == [(0, tmp_path / "a.docx")]
        assert chunk_res.success == [(1, out_dir / "b.pdf")]

    def test_uses_unique_path_for_output(self, env, tmp_path):
        converter, _ = env
        out_dir = tmp_path / "out"
        unique = out_dir / "a (1).pdf"
        chunk_res = ConversionResult()

        with patch.object(mod, "get_unique_path", return_value=unique) as unique_mock:
            converter._convert_chunk_files(
                app=MagicMock(),
                app_type=OfficeApp.WORD,
                chunk=[(0, tmp_path / "a.docx")],
                tmp_dir=tmp_path / "tmp",
                out_dir=out_dir,
                chunk_res=chunk_res,
            )

        unique_mock.assert_called_once_with(out_dir / "a.pdf")
        assert chunk_res.success == [(0, unique)]

    def test_stop_signal_propagates(self, env, tmp_path):
        converter, processor = env
        converter.check_stop = MagicMock(side_effect=InterruptedError)
        chunk_res = ConversionResult()

        with pytest.raises(InterruptedError):
            converter._convert_chunk_files(
                app=MagicMock(),
                app_type=OfficeApp.WORD,
                chunk=[(0, tmp_path / "a.docx")],
                tmp_dir=tmp_path / "tmp",
                out_dir=tmp_path / "out",
                chunk_res=chunk_res,
            )

        processor.assert_not_called()
        assert chunk_res.success == []
        assert chunk_res.failed == []


class TestProcessChunk:
    @pytest.fixture
    def env(self, converter):
        app = MagicMock()
        converter._get_app_instance = MagicMock(return_value=app)
        converter._disable_visibility = MagicMock()
        converter._convert_chunk_files = MagicMock()
        converter._safe_release_com_object = MagicMock()
        return converter, app

    def test_success_flow(self, env, tmp_path):
        converter, app = env
        chunk = [(0, tmp_path / "a.docx")]

        with patch.object(mod, "pythoncom") as com:
            result = converter._process_chunk(
                chunk=chunk, app_type=OfficeApp.WORD, out_dir=tmp_path
            )

        converter._get_app_instance.assert_called_once_with(app_type=OfficeApp.WORD)
        converter._disable_visibility.assert_called_once_with(
            app=app, app_type=OfficeApp.WORD
        )
        kwargs = converter._convert_chunk_files.call_args.kwargs
        assert kwargs["app"] is app
        assert kwargs["app_type"] == OfficeApp.WORD
        assert kwargs["chunk"] == chunk
        assert kwargs["out_dir"] == tmp_path
        assert isinstance(kwargs["tmp_dir"], Path)
        assert kwargs["chunk_res"] is result
        converter._safe_release_com_object.assert_called_once_with(
            obj=app, app_type=OfficeApp.WORD
        )
        com.CoInitialize.assert_called_once()
        com.CoUninitialize.assert_called_once()

    def test_app_not_created_marks_all_failed(self, env, tmp_path):
        converter, _ = env
        converter._get_app_instance.return_value = None
        chunk = [(0, tmp_path / "a.docx"), (1, tmp_path / "b.docx")]

        with patch.object(mod, "pythoncom") as com:
            result = converter._process_chunk(
                chunk=chunk, app_type=OfficeApp.WORD, out_dir=tmp_path
            )

        converter._convert_chunk_files.assert_not_called()
        assert result.success == []
        assert result.failed == chunk
        converter._safe_release_com_object.assert_called_once_with(
            obj=None, app_type=OfficeApp.WORD
        )
        com.CoUninitialize.assert_called_once()

    def test_unexpected_error_marks_only_unprocessed_as_failed(self, env, tmp_path):
        converter, _ = env
        chunk = [(0, tmp_path / "a.docx"), (1, tmp_path / "b.docx")]

        def die_midway(**kwargs):
            kwargs["chunk_res"].success.append((0, Path("0.pdf")))
            raise RuntimeError("COM died")

        converter._convert_chunk_files.side_effect = die_midway

        with patch.object(mod, "pythoncom"):
            result = converter._process_chunk(
                chunk=chunk, app_type=OfficeApp.WORD, out_dir=tmp_path
            )

        assert result.success == [(0, Path("0.pdf"))]
        assert result.failed == [(1, tmp_path / "b.docx")]

    def test_interrupted_error_propagates_but_cleans_up(self, env, tmp_path):
        converter, app = env
        converter._convert_chunk_files.side_effect = InterruptedError

        with patch.object(mod, "pythoncom") as com, pytest.raises(InterruptedError):
            converter._process_chunk(
                chunk=[(0, tmp_path / "a.docx")],
                app_type=OfficeApp.WORD,
                out_dir=tmp_path,
            )

        converter._safe_release_com_object.assert_called_once_with(
            obj=app, app_type=OfficeApp.WORD
        )
        com.CoUninitialize.assert_called_once()


class TestRunConversion:
    def test_success_returns_output_path(self, converter, tmp_path):
        src = touch(tmp_path / "a.docx")
        out = tmp_path / "a.pdf"
        func = MagicMock()

        result = converter._run_conversion(
            file_path=src, conversion_func=func, output_path=out
        )

        func.assert_called_once_with(src.resolve(), out)
        assert result == out

    def test_failure_removes_partial_output_and_reraises(self, converter, tmp_path):
        src = touch(tmp_path / "a.docx")
        out = touch(tmp_path / "a.pdf")
        func = MagicMock(side_effect=RuntimeError("export failed"))

        with pytest.raises(RuntimeError, match="export failed"):
            converter._run_conversion(
                file_path=src, conversion_func=func, output_path=out
            )

        assert not out.exists()

    def test_failure_without_output_file_still_reraises(self, converter, tmp_path):
        src = touch(tmp_path / "a.docx")
        out = tmp_path / "a.pdf"
        func = MagicMock(side_effect=RuntimeError("export failed"))

        with pytest.raises(RuntimeError, match="export failed"):
            converter._run_conversion(
                file_path=src, conversion_func=func, output_path=out
            )


class TestConvertPresToPdf:
    def test_success(self, converter, tmp_path):
        src = touch(tmp_path / "a.pptx")
        out = tmp_path / "a.pdf"
        app = MagicMock()
        pres = app.Presentations.Open.return_value

        result = converter._convert_pres_to_pdf(app=app, file_path=src, output_path=out)

        app.Presentations.Open.assert_called_once_with(
            str(src.resolve()), ReadOnly=True, WithWindow=0
        )
        pres.SaveAs.assert_called_once_with(str(out), 32)
        pres.Close.assert_called_once()
        assert result == out

    def test_closes_presentation_and_cleans_up_on_error(self, converter, tmp_path):
        src = touch(tmp_path / "a.pptx")
        out = touch(tmp_path / "a.pdf")
        app = MagicMock()
        pres = app.Presentations.Open.return_value
        pres.SaveAs.side_effect = RuntimeError("save failed")

        with pytest.raises(RuntimeError, match="save failed"):
            converter._convert_pres_to_pdf(app=app, file_path=src, output_path=out)

        pres.Close.assert_called_once()
        assert not out.exists()


class TestConvertTableToPdf:
    def test_success(self, converter, tmp_path):
        src = touch(tmp_path / "a.xlsx")
        out = tmp_path / "a.pdf"
        app = MagicMock()
        wb = app.Workbooks.Open.return_value
        converter._prepare_table_for_export = MagicMock()

        result = converter._convert_table_to_pdf(
            app=app, file_path=src, output_path=out
        )

        app.Workbooks.Open.assert_called_once_with(str(src.resolve()), ReadOnly=True)
        converter._prepare_table_for_export.assert_called_once_with(wb=wb)
        wb.ExportAsFixedFormat.assert_called_once_with(0, str(out))
        wb.Close.assert_called_once_with(SaveChanges=False)
        assert result == out

    def test_closes_workbook_and_cleans_up_on_error(self, converter, tmp_path):
        src = touch(tmp_path / "a.xlsx")
        out = touch(tmp_path / "a.pdf")
        app = MagicMock()
        wb = app.Workbooks.Open.return_value
        wb.ExportAsFixedFormat.side_effect = RuntimeError("export failed")
        converter._prepare_table_for_export = MagicMock()

        with pytest.raises(RuntimeError, match="export failed"):
            converter._convert_table_to_pdf(app=app, file_path=src, output_path=out)

        wb.Close.assert_called_once_with(SaveChanges=False)
        assert not out.exists()

    def test_prepare_error_still_closes_workbook(self, converter, tmp_path):
        src = touch(tmp_path / "a.xlsx")
        app = MagicMock()
        wb = app.Workbooks.Open.return_value
        converter._prepare_table_for_export = MagicMock(
            side_effect=ValueError("bad sheet")
        )

        with pytest.raises(ValueError, match="bad sheet"):
            converter._convert_table_to_pdf(
                app=app, file_path=src, output_path=tmp_path / "a.pdf"
            )

        wb.ExportAsFixedFormat.assert_not_called()
        wb.Close.assert_called_once_with(SaveChanges=False)


class TestConvertDocToPdf:
    def test_success(self, converter, tmp_path):
        src = touch(tmp_path / "a.docx")
        out = tmp_path / "a.pdf"
        app = MagicMock()
        doc = app.Documents.Open.return_value

        result = converter._convert_doc_to_pdf(app=app, file_path=src, output_path=out)

        app.Documents.Open.assert_called_once_with(
            str(src.resolve()), ReadOnly=True, ConfirmConversions=False
        )
        doc.ExportAsFixedFormat.assert_called_once_with(str(out), 17)
        doc.Close.assert_called_once_with(SaveChanges=0)
        assert result == out

    def test_closes_document_and_cleans_up_on_error(self, converter, tmp_path):
        src = touch(tmp_path / "a.docx")
        out = touch(tmp_path / "a.pdf")
        app = MagicMock()
        doc = app.Documents.Open.return_value
        doc.ExportAsFixedFormat.side_effect = RuntimeError("export failed")

        with pytest.raises(RuntimeError, match="export failed"):
            converter._convert_doc_to_pdf(app=app, file_path=src, output_path=out)

        doc.Close.assert_called_once_with(SaveChanges=0)
        assert not out.exists()


class TestSafeReleaseComObject:
    def test_quits_application(self, converter):
        app = MagicMock()

        converter._safe_release_com_object(obj=app, app_type="Word")

        app.Quit.assert_called_once()

    def test_none_is_ignored(self, converter):
        converter._safe_release_com_object(obj=None)

    def test_object_without_quit_is_ignored(self, converter):
        converter._safe_release_com_object(obj=MagicMock(spec=[]))

    def test_quit_error_is_logged_not_raised(self, converter, caplog):
        app = MagicMock()
        app.Quit.side_effect = RuntimeError("busy")

        with caplog.at_level(logging.WARNING):
            converter._safe_release_com_object(obj=app, app_type="Excel")

        assert "Could not close Excel gracefully" in caplog.text
