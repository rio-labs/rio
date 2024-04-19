import threading
from typing import *  # type: ignore

T = TypeVar("T")


class ThreadsafeFuture(Generic[T]):
    def __init__(self) -> None:
        self._result_value: Any
        self._event = threading.Event()

    def set_result(self, result: T) -> None:
        self._result_value = result
        self._event.set()

    def result(self) -> T:
        self._event.wait()
        return self._result_value

    def done(self) -> bool:
        return self._event.is_set()
