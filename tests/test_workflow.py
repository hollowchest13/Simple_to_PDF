# pyright: reportAttributeAccessIssue=false, reportArgumentType=false
import logging
import queue
import sys
import threading
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest

from simple_to_pdf.core.workflow import WorkflowManager
from simple_to_pdf.pdf import PageExtractor, PDFCompressor, PdfMerger
from simple_to_pdf.utils.process_tools import run_service_method_in_process

FILES = [(1, Path("a.docx")), (2, Path("b.pdf"))]


# --------------------------------------------------------------------------
# Хелпери та фікстури
# --------------------------------------------------------------------------
def make_service() -> MagicMock:
    """Сервіс-заглушка зі справжнім (не встановленим) stop_event."""
    svc = MagicMock()
    svc.stop_event = threading.Event()
    return svc


def make_executor() -> MagicMock:
    ex = MagicMock()
    ex._shutdown = False  # інакше MagicMock-атрибут буде truthy
    ex._processes = {}
    return ex


def done_future(result=None, exception: Exception | None = None) -> Future:
    future: Future = Future()
    if exception is not None:
        future.set_exception(exception)
    else:
        future.set_result(result)
    return future


def workflow_module():
    return sys.modules[WorkflowManager.__module__]


def stage_events(manager: WorkflowManager) -> list[str]:
    # Явно кажемо статичному аналізатору, що це мок-об'єкт
    callback_mock = cast(MagicMock, manager.callback)

    return [
        c.kwargs["stage"]
        for c in callback_mock.call_args_list
        if c.args and c.args[0] == "progress" and "stage" in c.kwargs
    ]


@pytest.fixture
def executor_cls(monkeypatch) -> MagicMock:
    """Підміна ProcessPoolExecutor: кожен виклик повертає новий фейковий executor."""
    cls = MagicMock(side_effect=lambda *a, **kw: make_executor())
    monkeypatch.setattr(workflow_module(), "ProcessPoolExecutor", cls)
    return cls


@pytest.fixture
def mp_manager(monkeypatch) -> MagicMock:
    """Підміна multiprocessing.Manager: звичайні Queue та Event без процесу-менеджера."""
    fake = MagicMock()
    fake.Queue.return_value = queue.Queue()
    fake.Event.return_value = threading.Event()
    monkeypatch.setattr(workflow_module().mp, "Manager", MagicMock(return_value=fake))
    return fake


@pytest.fixture
def make_manager(executor_cls, mp_manager):
    """Фабрика WorkflowManager БЕЗ встановленого callback."""

    def _make() -> WorkflowManager:
        return WorkflowManager(
            conversion_service=make_service(),
            merger_service=make_service(),
            compressor_service=make_service(),
            page_extractor_service=make_service(),
        )

    return _make


@pytest.fixture
def manager(make_manager) -> WorkflowManager:
    m = make_manager()
    m.callback = MagicMock()
    return m


def _fake_execute(**kwargs):
    """Імітація execute_in_process: створює вихідний файл і повертає його шлях.
    Вміст файлу = назва методу, тож видно, який етап його створив."""
    kw = kwargs["method_kwargs"]
    out = Path(kw.get("output_file") or kw["output_path"])
    out.write_bytes(kwargs["method_name"].encode())
    return out


@pytest.fixture
def fake_execute(manager) -> MagicMock:
    manager.execute_in_process = MagicMock(side_effect=_fake_execute)
    return manager.execute_in_process


# --------------------------------------------------------------------------
# __init__
# --------------------------------------------------------------------------
class TestInit:
    def test_uses_provided_services(self, manager):
        assert manager.services == [
            manager.merger,
            manager.compressor,
            manager.converter,
            manager.extractor,
        ]

    def test_creates_default_services_when_none_given(
        self, executor_cls, mp_manager, monkeypatch
    ):
        module = workflow_module()
        for name in (
            "ConversionService",
            "PdfMerger",
            "PDFCompressor",
            "PageExtractor",
        ):
            monkeypatch.setattr(module, name, MagicMock())

        m = WorkflowManager()

        module.ConversionService.assert_called_once_with()
        module.PdfMerger.assert_called_once_with()
        module.PDFCompressor.assert_called_once_with()
        module.PageExtractor.assert_called_once_with()
        assert m.converter is module.ConversionService.return_value

    def test_creates_executor_with_two_workers(self, executor_cls, manager):
        executor_cls.assert_called_once_with(max_workers=2)
        assert manager._workers == 2

    def test_queue_and_event_come_from_mp_manager(self, manager, mp_manager):
        assert manager._mp_queue is mp_manager.Queue.return_value
        assert manager._stop_event is mp_manager.Event.return_value


# --------------------------------------------------------------------------
# callback (property)
# --------------------------------------------------------------------------
class TestCallbackProperty:
    def test_getter_returns_set_value(self, manager):
        cb = MagicMock()

        manager.callback = cb

        assert manager.callback is cb

    def test_none_is_replaced_with_noop(self, manager):
        manager.callback = None

        assert manager.callback is not None
        assert manager.callback("progress", stage="x") is None

    @pytest.mark.xfail(
        strict=True,
        reason="БАГ: _callback не ініціалізується в __init__, тож звернення до "
        "manager.callback до виклику сеттера кидає AttributeError. Виправлення: "
        "додати `self.callback = None` в кінець __init__. Приберіть xfail "
        "після виправлення.",
    )
    def test_default_callback_is_noop(self, make_manager):
        m = make_manager()

        assert m.callback("progress", stage="x") is None


# --------------------------------------------------------------------------
# manage_services / _is_cancelled
# --------------------------------------------------------------------------
class TestManageServices:
    def test_stop_sets_event(self, manager):
        manager.manage_services(action="stop")

        assert manager._stop_event.is_set()

    def test_reset_clears_event(self, manager):
        manager._stop_event.set()

        manager.manage_services(action="reset")

        assert not manager._stop_event.is_set()

    @pytest.mark.parametrize("action", ["stop", "reset"])
    def test_shared_event_is_assigned_to_services(self, manager, action):
        manager.manage_services(action=action)

        assert all(s.stop_event is manager._stop_event for s in manager.services)

    def test_services_without_stop_event_are_untouched(self, manager):
        with_event = SimpleNamespace(stop_event=None)
        without_event = SimpleNamespace()
        manager.services = [with_event, without_event, None]

        manager.manage_services(action="stop")

        assert with_event.stop_event is manager._stop_event
        assert not hasattr(without_event, "stop_event")


class TestIsCancelled:
    def test_false_when_no_event_set(self, manager):
        assert manager._is_cancelled() is False

    def test_true_when_any_service_event_set(self, manager):
        manager.compressor.stop_event.set()

        assert manager._is_cancelled() is True

    def test_services_without_stop_event_and_none_are_skipped(self, manager):
        manager.services = [None, SimpleNamespace()]

        assert manager._is_cancelled() is False

    def test_stop_action_makes_manager_cancelled(self, manager):
        manager.manage_services(action="stop")

        assert manager._is_cancelled() is True

    def test_reset_action_clears_cancellation(self, manager):
        manager.manage_services(action="stop")
        manager.manage_services(action="reset")

        assert manager._is_cancelled() is False


# --------------------------------------------------------------------------
# _get_executor / kill_executor / close_mp_manager
# --------------------------------------------------------------------------
class TestExecutorLifecycle:
    def test_get_executor_returns_existing(self, manager, executor_cls):
        existing = manager._process_executor

        assert manager._get_executor() is existing
        assert executor_cls.call_count == 1  # лише з __init__

    def test_get_executor_creates_when_none(self, manager, executor_cls):
        manager._process_executor = None

        result = manager._get_executor()

        assert result is manager._process_executor
        assert executor_cls.call_count == 2
        executor_cls.assert_called_with(max_workers=2)

    def test_get_executor_recreates_after_shutdown(self, manager):
        old = manager._process_executor
        old._shutdown = True

        new = manager._get_executor()

        assert new is not old
        assert manager._process_executor is new

    def test_kill_executor_does_nothing_when_none(self, manager):
        manager._process_executor = None

        manager.kill_executor()  # не має кидати

        assert manager._process_executor is None

    def test_kill_executor_terminates_only_alive_processes(self, manager):
        alive, dead = MagicMock(), MagicMock()
        alive.is_alive.return_value = True
        dead.is_alive.return_value = False
        executor = manager._process_executor
        executor._processes = {1: alive, 2: dead, 3: None}

        manager.kill_executor()

        alive.terminate.assert_called_once_with()
        dead.terminate.assert_not_called()
        executor.shutdown.assert_called_once_with(wait=False, cancel_futures=True)
        assert manager._process_executor is None

    def test_kill_executor_handles_non_dict_processes(self, manager):
        executor = manager._process_executor
        executor._processes = ["not", "a", "dict"]

        manager.kill_executor()

        executor.shutdown.assert_called_once_with(wait=False, cancel_futures=True)
        assert manager._process_executor is None

    def test_kill_executor_logs_errors_and_resets(self, manager, caplog):
        executor = manager._process_executor
        executor.shutdown.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            manager.kill_executor()

        assert "Error while killing process executor!" in caplog.text
        assert manager._process_executor is None

    def test_executor_can_be_recreated_after_kill(self, manager):
        manager.kill_executor()

        assert manager._get_executor() is manager._process_executor
        assert manager._process_executor is not None


close_mp_bug = pytest.mark.xfail(
    strict=True,
    reason="БАГ: close_mp_manager перевіряє hasattr(self, 'mp_manager'), а "
    "атрибут називається '_mp_manager', тому shutdown() ніколи не викликається. "
    "Виправлення: hasattr(self, '_mp_manager'). Приберіть xfail після виправлення.",
)


class TestCloseMpManager:
    @close_mp_bug
    def test_shutdown_is_called(self, manager, mp_manager):
        manager.close_mp_manager()

        mp_manager.shutdown.assert_called_once_with()

    @close_mp_bug
    def test_shutdown_error_is_swallowed_and_logged(self, manager, mp_manager, caplog):
        mp_manager.shutdown.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            manager.close_mp_manager()  # не має кидати

        assert "Shutdown multiprocessing error!" in caplog.text


# --------------------------------------------------------------------------
# execute_in_process
# --------------------------------------------------------------------------
class TestExecuteInProcess:
    def run(self, manager, ui=None, **overrides):
        kwargs = {
            "ui_callback": ui or MagicMock(),
            "service_cls": PdfMerger,
            "method_name": "merge_to_pdf",
            "method_kwargs": {"a": 1},
            "stop_event": manager._stop_event,
            "poll_interval": 0.001,
        }
        kwargs.update(overrides)
        return manager.execute_in_process(**kwargs)

    def test_returns_future_result(self, manager):
        manager._process_executor.submit.return_value = done_future("result")

        assert self.run(manager) == "result"

    def test_submits_task_with_expected_arguments(self, manager):
        manager._process_executor.submit.return_value = done_future("ok")
        method_kwargs = {"x": 1}

        self.run(
            manager,
            method_kwargs=method_kwargs,
            method_name="compress",
            service_cls=PDFCompressor,
        )

        manager._process_executor.submit.assert_called_once_with(
            run_service_method_in_process,
            service_cls=PDFCompressor,
            method_name="compress",
            method_kwargs=method_kwargs,
            mp_queue=manager._mp_queue,
            callback_attr="_show_callback",
            stop_event=manager._stop_event,
        )

    def test_custom_callback_attr_is_forwarded(self, manager):
        manager._process_executor.submit.return_value = done_future("ok")

        self.run(manager, callback_attr="_my_callback")

        assert (
            manager._process_executor.submit.call_args.kwargs["callback_attr"]
            == "_my_callback"
        )

    def test_queued_messages_are_forwarded_to_ui_callback(self, manager):
        manager._process_executor.submit.return_value = done_future("ok")
        manager._mp_queue.put(
            {"event_type": "progress", "params": {"stage": "merging", "current": 1}}
        )
        manager._mp_queue.put(
            {"event_type": "status", "params": {"key": "x", "status": "info"}}
        )
        ui = MagicMock()

        self.run(manager, ui=ui)

        assert ui.call_args_list == [
            (("progress",), {"stage": "merging", "current": 1}),
            (("status",), {"key": "x", "status": "info"}),
        ]

    def test_messages_posted_while_waiting_and_right_before_finish_are_delivered(
        self, manager
    ):
        future: Future = Future()
        manager._process_executor.submit.return_value = future
        msg1 = {"event_type": "progress", "params": {"current": 1}}
        msg2 = {"event_type": "progress", "params": {"current": 2}}
        manager._mp_queue.put(msg1)

        def finish():
            manager._mp_queue.put(msg2)  # прийшло безпосередньо перед завершенням
            future.set_result("done")

        timer = threading.Timer(0.05, finish)
        timer.start()
        ui = MagicMock()

        try:
            result = self.run(manager, ui=ui)
        finally:
            timer.cancel()

        assert result == "done"
        assert ui.call_args_list == [
            (("progress",), {"current": 1}),
            (("progress",), {"current": 2}),
        ]

    def test_empty_race_on_queue_does_not_hang_or_crash(self, manager):
        class FlakyQueue:
            """empty() каже, що є дані, але get_nowait() кидає Empty."""

            def __init__(self):
                self.polled = False

            def empty(self):
                return self.polled

            def get_nowait(self):
                self.polled = True
                raise queue.Empty

        manager._mp_queue = FlakyQueue()
        manager._process_executor.submit.return_value = done_future("ok")

        assert self.run(manager) == "ok"

    def test_exception_from_future_is_propagated(self, manager):
        manager._process_executor.submit.return_value = done_future(
            exception=ValueError("bad pdf")
        )

        with pytest.raises(ValueError, match="bad pdf"):
            self.run(manager)

    def test_remaining_messages_are_delivered_even_if_task_fails(self, manager):
        manager._process_executor.submit.return_value = done_future(
            exception=RuntimeError("crash")
        )
        manager._mp_queue.put({"event_type": "status", "params": {"key": "last"}})
        ui = MagicMock()

        with pytest.raises(RuntimeError):
            self.run(manager, ui=ui)

        ui.assert_called_once_with("status", key="last")

    def test_submit_runtime_error_becomes_interrupted_error(self, manager, caplog):
        original = RuntimeError("cannot schedule new futures after shutdown")
        manager._process_executor.submit.side_effect = original

        with (
            caplog.at_level(logging.WARNING),
            pytest.raises(InterruptedError, match="no longer active") as exc_info,
        ):
            self.run(manager)

        assert exc_info.value.__cause__ is original
        assert "Failed to submit task" in caplog.text

    def test_creates_executor_when_missing(self, manager):
        manager._process_executor = None
        new_executor = make_executor()
        new_executor.submit.return_value = done_future("ok")
        workflow_module().ProcessPoolExecutor.side_effect = None
        workflow_module().ProcessPoolExecutor.return_value = new_executor

        result = self.run(manager)

        assert result == "ok"
        assert manager._process_executor is new_executor


# --------------------------------------------------------------------------
# extract_pages
# --------------------------------------------------------------------------
class TestExtractPages:
    def run(self, manager, tmp_path, *, need_compress=False, pages=None):
        out = tmp_path / "result.pdf"
        manager.extract_pages(
            input_path=tmp_path / "in.pdf",
            pages=pages or [1, 3],
            output_path=out,
            need_compress=need_compress,
        )
        return out

    def test_runs_extractor_with_expected_arguments(
        self, manager, fake_execute, tmp_path
    ):
        self.run(manager, tmp_path, pages=[2, 4])

        kwargs = fake_execute.call_args.kwargs
        assert kwargs["service_cls"] is PageExtractor
        assert kwargs["method_name"] == "extract_pages"
        assert kwargs["ui_callback"] is manager.callback
        assert kwargs["stop_event"] is manager._stop_event
        method_kwargs = kwargs["method_kwargs"]
        assert method_kwargs["input_file"] == tmp_path / "in.pdf"
        assert method_kwargs["pages_to_extract"] == [2, 4]
        assert method_kwargs["output_file"].name == "extracted.pdf"

    def test_result_is_moved_to_output_path(self, manager, fake_execute, tmp_path):
        out = self.run(manager, tmp_path)

        assert out.exists()
        assert out.read_bytes() == b"extract_pages"
        fake_execute.assert_called_once()  # без стиснення

    def test_saving_done_status_is_sent(self, manager, fake_execute, tmp_path):
        out = self.run(manager, tmp_path)

        manager.callback.assert_called_with(
            "status", key="saving.done", status="info", path=out
        )

    def test_with_compression_final_file_is_compressed(
        self, manager, fake_execute, tmp_path
    ):
        out = self.run(manager, tmp_path, need_compress=True)

        assert fake_execute.call_count == 2
        first, second = (c.kwargs for c in fake_execute.call_args_list)
        assert first["method_name"] == "extract_pages"
        assert second["service_cls"] is PDFCompressor
        assert second["method_name"] == "compress"
        assert second["method_kwargs"]["input_pdf_path"].name == "extracted.pdf"
        assert second["method_kwargs"]["output_path"].name == "compressed.pdf"
        assert out.read_bytes() == b"compress"

    def test_compression_progress_is_reported_only_when_requested(
        self, manager, fake_execute, tmp_path
    ):
        self.run(manager, tmp_path, need_compress=False)
        assert "compressing" not in stage_events(manager)

        manager.callback.reset_mock()
        self.run(manager, tmp_path, need_compress=True)
        assert "compressing" in stage_events(manager)

    def test_interruption_is_propagated_and_logged(
        self, manager, fake_execute, tmp_path, caplog
    ):
        fake_execute.side_effect = InterruptedError()

        with caplog.at_level(logging.WARNING), pytest.raises(InterruptedError):
            self.run(manager, tmp_path)

        assert "Page extraction canceled by user!" in caplog.text
        assert not (tmp_path / "result.pdf").exists()

    def test_value_error_is_propagated_without_error_log(
        self, manager, fake_execute, tmp_path, caplog
    ):
        fake_execute.side_effect = ValueError("No pages selected")

        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="No pages selected"),
        ):
            self.run(manager, tmp_path)

        assert "Error during page extraction" not in caplog.text

    def test_other_errors_are_logged_and_reraised(
        self, manager, fake_execute, tmp_path, caplog
    ):
        fake_execute.side_effect = RuntimeError("disk exploded")

        with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
            self.run(manager, tmp_path)

        assert "Error during page extraction: disk exploded" in caplog.text

    def test_no_saving_status_on_failure(self, manager, fake_execute, tmp_path):
        fake_execute.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            self.run(manager, tmp_path)

        assert not any(
            c.kwargs.get("key") == "saving.done"
            for c in manager.callback.call_args_list
        )


# --------------------------------------------------------------------------
# merge_files
# --------------------------------------------------------------------------
class TestMergeFiles:
    def run(self, manager, tmp_path, *, need_compress=False, target_format=None):
        out = tmp_path / "result.pdf"
        manager.merge_files(
            files=FILES,
            output_path=out,
            need_compress=need_compress,
            target_format=target_format,
        )
        return out

    def test_converts_files_into_temp_dir(self, manager, fake_execute, tmp_path):
        self.run(manager, tmp_path)

        manager.converter.get_conversion_rep.assert_called_once()
        kwargs = manager.converter.get_conversion_rep.call_args.kwargs
        assert kwargs["files"] == FILES
        assert isinstance(kwargs["out_dir"], Path)

    def test_runs_merger_with_conversion_report(self, manager, fake_execute, tmp_path):
        self.run(manager, tmp_path, target_format="A4")

        fake_execute.assert_called_once()
        kwargs = fake_execute.call_args.kwargs
        assert kwargs["service_cls"] is PdfMerger
        assert kwargs["method_name"] == "merge_to_pdf"
        assert kwargs["ui_callback"] is manager.callback
        assert kwargs["stop_event"] is manager._stop_event
        method_kwargs = kwargs["method_kwargs"]
        assert (
            method_kwargs["conversion_rep"]
            is manager.converter.get_conversion_rep.return_value
        )
        assert method_kwargs["target_page_format"] == "A4"
        assert method_kwargs["output_path"].name == "merged.pdf"

    def test_without_compression_only_merger_runs(
        self, manager, fake_execute, tmp_path
    ):
        self.run(manager, tmp_path, need_compress=False)

        assert fake_execute.call_count == 1
        assert stage_events(manager) == ["analyzing", "merging"]

    def test_with_compression_compressor_gets_merged_file(
        self, manager, fake_execute, tmp_path
    ):
        self.run(manager, tmp_path, need_compress=True)

        assert fake_execute.call_count == 2
        second = fake_execute.call_args_list[1].kwargs
        assert second["service_cls"] is PDFCompressor
        assert second["method_name"] == "compress"
        assert second["method_kwargs"]["input_pdf_path"].name == "merged.pdf"
        assert second["method_kwargs"]["output_path"].name == "compressed.pdf"
        assert stage_events(manager) == ["analyzing", "merging", "compressing"]

    def test_saving_done_status_is_sent(self, manager, fake_execute, tmp_path):
        out = self.run(manager, tmp_path)

        manager.callback.assert_any_call(
            "status", key="saving.done", status="info", path=out
        )

    def test_cancelled_after_conversion_stops_before_merge(
        self, manager, fake_execute, tmp_path, caplog
    ):
        manager._is_cancelled = MagicMock(return_value=True)

        with caplog.at_level(logging.WARNING), pytest.raises(InterruptedError):
            self.run(manager, tmp_path)

        fake_execute.assert_not_called()
        assert "File merge canceled by user!" in caplog.text

    def test_cancelled_after_merge_skips_compression(
        self, manager, fake_execute, tmp_path
    ):
        manager._is_cancelled = MagicMock(side_effect=[False, True])

        with pytest.raises(InterruptedError):
            self.run(manager, tmp_path, need_compress=True)

        assert fake_execute.call_count == 1  # лише merger

    def test_conversion_error_is_logged_and_reraised(
        self, manager, fake_execute, tmp_path, caplog
    ):
        manager.converter.get_conversion_rep.side_effect = RuntimeError("no office")

        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(RuntimeError, match="no office"),
        ):
            self.run(manager, tmp_path)

        assert "Merge stage failed!" in caplog.text
        fake_execute.assert_not_called()

    def test_merger_error_is_logged_and_reraised(
        self, manager, fake_execute, tmp_path, caplog
    ):
        fake_execute.side_effect = ValueError("No PDF data")

        with caplog.at_level(logging.ERROR), pytest.raises(ValueError):
            self.run(manager, tmp_path)

        assert "Merge stage failed!" in caplog.text

    def test_interruption_from_worker_is_propagated(
        self, manager, fake_execute, tmp_path
    ):
        fake_execute.side_effect = InterruptedError()

        with pytest.raises(InterruptedError):
            self.run(manager, tmp_path)

    @pytest.mark.xfail(
        strict=True,
        reason="БАГ: merge_files не переміщує результат у output_path. Файл "
        "залишається в тимчасовій теці, яка видаляється при виході з `with`, "
        "хоча статус 'saving.done' уже надіслано. Виправлення: перед статусом "
        "saving.done додати shutil.move(merged_pdf_path, output_path) (як в "
        "extract_pages). Приберіть xfail після виправлення.",
    )
    @pytest.mark.parametrize(
        ("need_compress", "expected"),
        [(False, b"merge_to_pdf"), (True, b"compress")],
    )
    def test_result_is_saved_to_output_path(
        self, manager, fake_execute, tmp_path, need_compress, expected
    ):
        out = self.run(manager, tmp_path, need_compress=need_compress)

        assert out.exists()
        assert out.read_bytes() == expected


# --------------------------------------------------------------------------
# _save_to_dest_dir
# --------------------------------------------------------------------------
class TestSaveToDestDir:
    def test_moves_file_and_reports_success(self, manager, tmp_path):
        src = tmp_path / "tmp.pdf"
        src.write_bytes(b"data")
        dst = tmp_path / "out" / "final.pdf"

        result = manager._save_to_dest_dir(input_path=src, output_path=dst)

        assert result is True
        assert dst.read_bytes() == b"data"
        assert not src.exists()

    def test_creates_missing_parent_directories(self, manager, tmp_path):
        src = tmp_path / "tmp.pdf"
        src.write_bytes(b"data")
        dst = tmp_path / "a" / "b" / "c" / "final.pdf"

        manager._save_to_dest_dir(input_path=src, output_path=dst)

        assert dst.exists()

    def test_success_callback_sequence(self, manager, tmp_path):
        src = tmp_path / "tmp.pdf"
        src.write_bytes(b"data")
        dst = tmp_path / "final.pdf"

        manager._save_to_dest_dir(input_path=src, output_path=dst)

        assert [c.args[0] for c in manager.callback.call_args_list] == [
            "progress",
            "status",
            "progress_reset",
            "status",
        ]
        first, last = (
            manager.callback.call_args_list[1],
            manager.callback.call_args_list[3],
        )
        assert first.kwargs == {
            "key": "saving_file",
            "status": "info",
            "filename": "final.pdf",
        }
        assert last.kwargs == {
            "key": "save_success",
            "status": "success",
            "filename": "final.pdf",
        }

    def test_failure_returns_false_and_reports_error(self, manager, tmp_path, caplog):
        missing = tmp_path / "missing.pdf"
        dst = tmp_path / "final.pdf"

        with caplog.at_level(logging.ERROR):
            result = manager._save_to_dest_dir(input_path=missing, output_path=dst)

        assert result is False
        assert "Failed to save file to" in caplog.text
        assert [c.args[0] for c in manager.callback.call_args_list][-2:] == [
            "progress_reset",
            "status",
        ]
        assert manager.callback.call_args_list[-1].kwargs == {
            "key": "save_error",
            "status": "error",
            "filename": "final.pdf",
        }
        assert not dst.exists()
