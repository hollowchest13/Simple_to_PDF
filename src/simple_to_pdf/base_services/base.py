from abc import ABC
import logging
import threading

logger = logging.getLogger(__name__)


class BaseService(ABC):
    def __init__(self):
        self._stop_event: threading.Event = threading.Event()

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
