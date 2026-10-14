import logging
from collections.abc import Callable
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
