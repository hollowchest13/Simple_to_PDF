import queue
import threading
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

import simple_to_pdf.core.workflow as wm
from simple_to_pdf.core.workflow import WorkflowManager


def _make_service() -> MagicMock:
    service = MagicMock()
    service.stop_event = threading.Event()
    return service


@pytest.fixture
def executor_cls(monkeypatch) -> MagicMock:
    """Mock of the ProcessPoolExecutor class (so that the type checker does not confuse it with the real one)."""
    cls_mock = MagicMock(name="ProcessPoolExecutor")
    monkeypatch.setattr(wm, "ProcessPoolExecutor", cls_mock)
    return cls_mock


@pytest.fixture
def manager(monkeypatch, executor_cls) -> WorkflowManager:
    """WorkflowManager without real processes and mp.Manager."""
    fake_mp = MagicMock()
    fake_mp.Manager.return_value.Event.return_value = threading.Event()
    fake_mp.Manager.return_value.Queue.return_value = queue.Queue()
    monkeypatch.setattr(wm, "mp", fake_mp)

    mgr = WorkflowManager(
        conversion_service=_make_service(),
        merger_service=_make_service(),
        compressor_service=_make_service(),
        page_extractor_service=_make_service(),
    )
    mgr.callback = MagicMock()
    return mgr


@pytest.fixture
def fake_execute(manager, monkeypatch):
    """Replaces execute_in_process: Creates an output file and records calls."""
    calls: list[dict] = []

    def _fake(**kwargs):
        calls.append(kwargs)
        out = kwargs["method_kwargs"].get("output_path") or kwargs["method_kwargs"].get(
            "output_file"
        )
        out = Path(out)
        out.write_text(kwargs["service_cls"].__name__)
        return out

    monkeypatch.setattr(manager, "execute_in_process", _fake)
    return calls


def _progress_stages(callback: MagicMock) -> list[str]:
    return [
        c.kwargs["stage"]
        for c in callback.call_args_list
        if c.args and c.args[0] == "progress" and "stage" in c.kwargs
    ]


class TestStopHandling:
    def test_stop_sets_event_and_shares_it_with_services(self, manager):
        manager.manage_services(action="stop")

        assert manager._stop_event.is_set()
        for service in manager.services:
            assert service.stop_event is manager._stop_event

    def test_reset_clears_event(self, manager):
        manager.manage_services(action="stop")
        manager.manage_services(action="reset")

        assert not manager._stop_event.is_set()

    def test_is_cancelled_true_after_stop(self, manager):
        manager.manage_services(action="stop")
        assert manager._is_cancelled() is True

    def test_is_cancelled_true_if_single_service_stopped(self, manager):
        manager.services[2].stop_event.set()
        assert manager._is_cancelled() is True


class TestSaveToDestDir:
    def test_moves_file_and_creates_parent_dirs(self, manager, tmp_path):
        src = tmp_path / "src.pdf"
        src.write_text("data")
        dst = tmp_path / "nested" / "dir" / "out.pdf"

        manager._save_to_dest_dir(input_path=src, output_path=dst)

        assert dst.read_text() == "data"
        assert not src.exists()

    def test_success_notifies_ui(self, manager, tmp_path):
        src = tmp_path / "src.pdf"
        src.write_text("data")
        dst = tmp_path / "out.pdf"

        manager._save_to_dest_dir(input_path=src, output_path=dst)

        manager.callback.assert_any_call(
            "progress", stage="saving", mode="indeterminate"
        )
        manager.callback.assert_any_call("progress_reset")

        status_calls = [
            call
            for call in manager.callback.call_args_list
            if call.args
            and call.args[0] == "status"
            and call.kwargs.get("status") == "success"
        ]
        assert len(status_calls) == 1
        assert status_calls[0].kwargs["path"] == dst

    def test_failure_notifies_ui_and_reraises(self, manager, tmp_path, monkeypatch):
        monkeypatch.setattr(
            wm.shutil, "move", MagicMock(side_effect=OSError("disk full"))
        )
        dst = tmp_path / "out.pdf"

        with pytest.raises(OSError, match="disk full"):
            manager._save_to_dest_dir(input_path=tmp_path / "x.pdf", output_path=dst)

        manager.callback.assert_any_call("progress_reset")

        error_calls = [
            call
            for call in manager.callback.call_args_list
            if call.args
            and call.args[0] == "status"
            and call.kwargs.get("status") == "error"
        ]
        assert len(error_calls) == 1
        assert error_calls[0].kwargs["path"] == dst


class TestMergeFiles:
    @pytest.fixture
    def files(self):
        return [(1, Path("a.docx")), (2, Path("b.png"))]

    def test_merge_without_compress(self, manager, fake_execute, files, tmp_path):
        out = tmp_path / "result" / "merged.pdf"
        manager.converter.get_conversion_rep.return_value = "REP"

        manager.merge_files(
            files=files, output_path=out, need_compress=False, target_format=None
        )

        assert out.read_text() == "PdfMerger"
        assert len(fake_execute) == 1
        merge_call = fake_execute[0]
        assert merge_call["service_cls"] is wm.PdfMerger
        assert merge_call["method_name"] == "merge_to_pdf"
        assert merge_call["stop_event"] is manager._stop_event
        assert merge_call["method_kwargs"]["conversion_rep"] == "REP"
        assert merge_call["method_kwargs"]["target_page_format"] is None
        assert _progress_stages(manager.callback) == [
            "analyzing",
            "merging",
            "saving",
        ]

    def test_merge_passes_files_to_converter(
        self, manager, fake_execute, files, tmp_path
    ):
        manager.merge_files(
            files=files,
            output_path=tmp_path / "o.pdf",
            need_compress=False,
            target_format=None,
        )

        kwargs = manager.converter.get_conversion_rep.call_args.kwargs
        assert kwargs["files"] == files
        assert isinstance(kwargs["out_dir"], Path)

    def test_merge_with_compress(self, manager, fake_execute, files, tmp_path):
        out = tmp_path / "merged.pdf"

        manager.merge_files(
            files=files, output_path=out, need_compress=True, target_format=None
        )

        assert [c["service_cls"] for c in fake_execute] == [
            wm.PdfMerger,
            wm.PDFCompressor,
        ]
        compress_call = fake_execute[1]
        assert compress_call["method_name"] == "compress"
        assert compress_call["method_kwargs"]["input_pdf_path"].name == "merged.pdf"
        assert out.read_text() == "PDFCompressor"
        assert "compressing" in _progress_stages(manager.callback)

    def test_cancelled_after_conversion(self, manager, fake_execute, files, tmp_path):
        manager.converter.get_conversion_rep.side_effect = lambda **kw: (
            manager.manage_services(action="stop")
        )
        out = tmp_path / "out.pdf"

        with pytest.raises(InterruptedError):
            manager.merge_files(
                files=files, output_path=out, need_compress=False, target_format=None
            )

        assert fake_execute == []
        assert not out.exists()

    def test_cancelled_after_merge_skips_compress_and_save(
        self, manager, monkeypatch, files, tmp_path
    ):
        def _fake(**kwargs):
            manager.manage_services(action="stop")
            p = kwargs["method_kwargs"]["output_path"]
            p.write_text("x")
            return p

        monkeypatch.setattr(manager, "execute_in_process", _fake)
        out = tmp_path / "out.pdf"

        with pytest.raises(InterruptedError):
            manager.merge_files(
                files=files, output_path=out, need_compress=True, target_format=None
            )

        assert not out.exists()

    def test_converter_error_is_propagated(self, manager, files, tmp_path):
        manager.converter.get_conversion_rep.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            manager.merge_files(
                files=files,
                output_path=tmp_path / "o.pdf",
                need_compress=False,
                target_format=None,
            )

    def test_merge_process_error_is_propagated(
        self, manager, monkeypatch, files, tmp_path
    ):
        monkeypatch.setattr(
            manager, "execute_in_process", MagicMock(side_effect=ValueError("bad"))
        )

        with pytest.raises(ValueError, match="bad"):
            manager.merge_files(
                files=files,
                output_path=tmp_path / "o.pdf",
                need_compress=False,
                target_format=None,
            )


class TestExtractPages:
    def test_extract_without_compress(self, manager, fake_execute, tmp_path):
        out = tmp_path / "res" / "extracted.pdf"

        manager.extract_pages(
            input_path=tmp_path / "in.pdf",
            pages=[1, 3],
            output_path=out,
            need_compress=False,
        )

        assert len(fake_execute) == 1
        extract_call = fake_execute[0]
        assert extract_call["service_cls"] is wm.PageExtractor
        assert extract_call["method_name"] == "extract_pages"
        assert extract_call["method_kwargs"]["pages_to_extract"] == [1, 3]
        assert extract_call["method_kwargs"]["input_file"] == tmp_path / "in.pdf"
        assert out.read_text() == "PageExtractor"

    def test_extract_with_compress(self, manager, fake_execute, tmp_path):
        out = tmp_path / "extracted.pdf"

        manager.extract_pages(
            input_path=tmp_path / "in.pdf",
            pages=[2],
            output_path=out,
            need_compress=True,
        )

        assert [c["service_cls"] for c in fake_execute] == [
            wm.PageExtractor,
            wm.PDFCompressor,
        ]
        assert (
            fake_execute[1]["method_kwargs"]["input_pdf_path"].name == "extracted.pdf"
        )
        assert out.read_text() == "PDFCompressor"
        assert "compressing" in _progress_stages(manager.callback)

    def test_cancelled_after_extraction(self, manager, monkeypatch, tmp_path):
        def _fake(**kwargs):
            manager.manage_services(action="stop")
            return kwargs["method_kwargs"]["output_file"]

        monkeypatch.setattr(manager, "execute_in_process", _fake)
        out = tmp_path / "out.pdf"

        with pytest.raises(InterruptedError):
            manager.extract_pages(
                input_path=tmp_path / "in.pdf",
                pages=[1],
                output_path=out,
                need_compress=False,
            )

        assert not out.exists()

    def test_value_error_is_reraised(self, manager, monkeypatch, tmp_path):
        monkeypatch.setattr(
            manager,
            "execute_in_process",
            MagicMock(side_effect=ValueError("invalid page")),
        )

        with pytest.raises(ValueError, match="invalid page"):
            manager.extract_pages(
                input_path=tmp_path / "in.pdf",
                pages=[99],
                output_path=tmp_path / "o.pdf",
                need_compress=False,
            )

    def test_generic_error_is_logged_and_reraised(
        self, manager, monkeypatch, tmp_path, caplog
    ):
        monkeypatch.setattr(
            manager, "execute_in_process", MagicMock(side_effect=OSError("io"))
        )

        with caplog.at_level("ERROR"), pytest.raises(OSError, match="io"):
            manager.extract_pages(
                input_path=tmp_path / "in.pdf",
                pages=[1],
                output_path=tmp_path / "o.pdf",
                need_compress=False,
            )

        assert "Error during page extraction" in caplog.text


class TestExecuteInProcess:
    @staticmethod
    def _run(manager, ui_callback, **overrides):
        kwargs = {
            "ui_callback": ui_callback,
            "service_cls": MagicMock,
            "method_name": "do",
            "method_kwargs": {"a": 1},
            "stop_event": manager._stop_event,
        }
        kwargs.update(overrides)
        return manager.execute_in_process(**kwargs)

    def test_returns_result_and_submits_with_correct_args(self, manager):
        done: Future = Future()
        done.set_result("RESULT")
        manager._process_executor.submit.return_value = done

        result = self._run(manager, MagicMock())

        assert result == "RESULT"
        submit = manager._process_executor.submit
        submit.assert_called_once_with(
            wm.run_service_method_in_process,
            service_cls=MagicMock,
            method_name="do",
            method_kwargs={"a": 1},
            mp_queue=manager._mp_queue,
            callback_attr="_show_callback",
            stop_event=manager._stop_event,
        )

    def test_forwards_queue_messages_to_ui_callback(self, manager):
        manager._mp_queue.put({"event_type": "progress", "params": {"value": 1}})
        manager._mp_queue.put({"event_type": "status", "params": {"key": "k"}})
        done: Future = Future()
        done.set_result(None)
        manager._process_executor.submit.return_value = done
        ui = MagicMock()

        self._run(manager, ui)

        assert ui.call_args_list == [
            call("progress", value=1),
            call("status", key="k"),
        ]

    def test_polls_until_future_done(self, manager, monkeypatch):
        sleep = MagicMock()
        monkeypatch.setattr(wm.time, "sleep", sleep)
        future = MagicMock()
        future.done.side_effect = [False, False, True]
        future.result.return_value = 42
        manager._process_executor.submit.return_value = future
        manager._mp_queue.put({"event_type": "progress", "params": {}})
        ui = MagicMock()

        result = self._run(manager, ui, poll_interval=0.5)

        assert result == 42
        assert sleep.call_count == 2
        sleep.assert_called_with(0.5)
        ui.assert_called_once_with("progress")

    def test_exception_from_process_is_propagated(self, manager):
        failed: Future = Future()
        failed.set_exception(ValueError("worker crashed"))
        manager._process_executor.submit.return_value = failed

        with pytest.raises(ValueError, match="worker crashed"):
            self._run(manager, MagicMock())

    def test_submit_runtime_error_becomes_interrupted_error(self, manager):
        manager._process_executor.submit.side_effect = RuntimeError("shutdown")

        with pytest.raises(InterruptedError, match="no longer active"):
            self._run(manager, MagicMock())

    def test_creates_executor_if_missing(self, manager, executor_cls):
        done: Future = Future()
        done.set_result("ok")
        new_executor = MagicMock()
        new_executor.submit.return_value = done
        executor_cls.return_value = new_executor
        manager._process_executor = None

        result = self._run(manager, MagicMock())

        assert result == "ok"
        assert manager._process_executor is new_executor
