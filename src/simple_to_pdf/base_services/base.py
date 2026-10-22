import logging  # noqa: I001
from abc import ABC
import multiprocessing as mp
from typing import Any

logger = logging.getLogger(__name__)


class BaseService(ABC):
    def __init__(self, *, stop_event: Any | None = None):
        self._stop_event: Any = stop_event or mp.Event()
        self._files_count = 0
        self.callback = None

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    @property
    def stop_event(self) -> Any:
        return self._stop_event

    @stop_event.setter
    def stop_event(self, value: Any):
        self._stop_event = value

    def check_stop(self):
        is_set = self._stop_event.is_set() if self._stop_event else False
        if is_set:
            logger.warning("Stop signal received")
            raise InterruptedError("Operation was cancelled by user.")

    def _show_callback(self, event_type: str, data: dict, force: bool = False):
        if force or self.should_show_callback():
            self.callback(event_type, **data)

    def should_show_callback(self) -> bool:
        return self._files_count > 1
