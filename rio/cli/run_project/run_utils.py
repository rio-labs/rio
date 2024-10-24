import threading
import typing as t

T = t.TypeVar("T")


class ThreadsafeFuture(t.Generic[T]):
    def __init__(self) -> None:
        self._result_value: t.Any
        self._event = threading.Event()

    def set_result(self, result: T) -> None:
        self._result_value = result
        self._event.set()

    def result(self) -> T:
        self._event.wait()
        return self._result_value

    def done(self) -> bool:
        return self._event.is_set()
