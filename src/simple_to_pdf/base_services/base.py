import logging
import threading
from abc import ABC

logger = logging.getLogger(__name__)


class BaseService(ABC):
    def __init__(self):
        self._stop_event: threading.Event = threading.Event()
        self._files_count = 0
        self.callback = None

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value if value is not None else lambda *args, **kwargs: None

    @property
    def stop_event(self) -> threading.Event:
        return self._stop_event

    @stop_event.setter
    def stop_event(self, value: threading.Event):
        self._stop_event = value

    def check_stop(self):
        if self.stop_event.is_set():
            logger.warning("Stop signal received")
            raise InterruptedError("Operation aborted")

    def _show_callback(self, event_type: str, data: dict, force: bool = False):
        if force or self.should_show_callback():
            self.callback(event_type, **data)

    def should_show_callback(self) -> bool:
        return self._files_count > 1
