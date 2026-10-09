import logging
import queue
import time
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def run_service_method_in_process(
    service_cls: type[T],
    method_name: str,
    method_kwargs: dict[str, Any],
    mp_queue: Any | None = None,
    callback_attr: str = "_show_callback",
) -> Any:
    """
    Adapted method for operation in a separate process
    """
    service_instance = service_cls()

    if mp_queue is not None:

        def _process_callback(
            event_type: str, data: dict[str, Any], force: bool = False
        ) -> None:
            mp_queue.put({"event_type": event_type, "params": data, "force": force})

        setattr(service_instance, callback_attr, _process_callback)

    method: Callable[..., Any] = getattr(service_instance, method_name)
    return method(**method_kwargs)


def execute_in_process(
    executor: ProcessPoolExecutor,
    mp_queue: Any,
    ui_callback: Any,
    service_cls: type[T],
    method_name: str,
    method_kwargs: dict[str, Any],
    callback_attr: str = "_show_callback",
    poll_interval: float = 0.02,
) -> Any:
    """
        Executed in a GUI background thread.
    Launches the task within the process and reads notifications from the `mp_queue` into the UI queue until completion.
    """
    try:
        future: Future[T] = executor.submit(
            run_service_method_in_process,
            service_cls=service_cls,
            method_name=method_name,
            method_kwargs=method_kwargs,
            mp_queue=mp_queue,
            callback_attr=callback_attr,
        )
    except RuntimeError as e:
        logger.warning(f"Failed to submit task to executor: {e}")
        raise InterruptedError("Process pool is no longer active.") from e

    # 1. Loop waiting for a Future to complete
    while not future.done():
        while not mp_queue.empty():
            try:
                msg = mp_queue.get_nowait()
                ui_callback.safe_callback(msg["event_type"], **msg["params"])
            except queue.Empty:
                break

        time.sleep(poll_interval)

    # 2. Read the remaining notifications from the queue after the process completes
    while not mp_queue.empty():
        try:
            msg = mp_queue.get_nowait()
            ui_callback.safe_callback(msg["event_type"], **msg["params"])
        except queue.Empty:
            break

    # 3. Return the result or raise an error if the process crashed
    return future.result()
