from __future__ import annotations

import collections.abc
import sys
import typing as t

import rio

from .. import global_state

__all__ = ["List", "Dict", "Set"]


T = t.TypeVar("T")


def identity(x: T) -> T:
    return x


class ObservableContainer:
    def __init__(self):
        self._affected_sessions: set[rio.Session] = set()

    def _mark_as_accessed(self):
        if global_state.currently_building_session is None:
            return

        global_state.accessed_objects.add(self)
        self._affected_sessions.add(global_state.currently_building_session)

    def _mark_as_changed(self) -> None:
        for session in self._affected_sessions:
            session._changed_objects.add(self)
            session._refresh_required_event.set()


class List(ObservableContainer, collections.abc.MutableSequence[T]):
    def __init__(self, items: t.Iterable[T] = (), /):
        super().__init__()

        self._items = list(items)

    def insert(self, index: int, value: T) -> None:
        self._items.insert(index, value)
        self._mark_as_changed()

    def append(self, value: T) -> None:
        self._items.append(value)
        self._mark_as_changed()

    def extend(self, values: t.Iterable[T]) -> None:
        self._items.extend(values)
        self._mark_as_changed()

    def remove(self, value: T) -> None:
        self._items.remove(value)
        self._mark_as_changed()

    def clear(self) -> None:
        self._items.clear()
        self._mark_as_changed()

    def pop(self, index: int | None = None, /) -> T:
        self._mark_as_accessed()

        if index is None:
            item = self._items.pop()
        else:
            item = self._items.pop(index)

        self._mark_as_changed()

        return item

    def reverse(self) -> None:
        self._items.reverse()
        self._mark_as_changed()

    def copy(self) -> List[T]:
        self._mark_as_accessed()
        return List(self)

    def __delitem__(self, index: int | slice) -> None:
        del self._items[index]
        self._mark_as_changed()

    def __add__(self, other: t.Iterable[T], /) -> List[T]:
        result = List(self)
        result += other
        return result

    def __iadd__(self, other: t.Iterable[T]) -> List[T]:
        self.extend(other)
        return self

    def index(self, value: T, start: int = 0, stop: int = sys.maxsize) -> int:
        self._mark_as_accessed()
        return self._items.index(value, start, stop)

    def count(self, value: T) -> int:
        self._mark_as_accessed()
        return self._items.count(value)

    @t.overload
    def __getitem__(self, index: int) -> T: ...

    @t.overload
    def __getitem__(self, index: slice) -> List[T]: ...

    def __getitem__(self, index: int | slice) -> T | List[T]:
        self._mark_as_accessed()

        if isinstance(index, slice):
            return List(self._items[index])
        else:
            return self._items[index]

    def __len__(self) -> int:
        self._mark_as_accessed()
        return len(self._items)

    def __iter__(self) -> t.Iterator[T]:
        # TODO: Technically, no data has been accessed yet. The correct behavior
        # would be to return a custom iterator that tracks access in its
        # `__next__` method.
        self._mark_as_accessed()
        return iter(self._items)

    def __contains__(self, value: object) -> bool:
        self._mark_as_accessed()
        return value in self._items

    # These function signatures are a PITA. Screw the boilerplate, just inherit
    # the signature
    if not t.TYPE_CHECKING:

        def sort(self, *args, **kwargs) -> None:
            self._items.sort(*args, **kwargs)
            self._mark_as_changed()

        def __setitem__(self, index_or_slice, value) -> None:
            self._items[index_or_slice] = value
            self._mark_as_changed()


K = t.TypeVar("K")
V = t.TypeVar("V")


class Dict(ObservableContainer, collections.abc.MutableMapping[K, V]):
    def __init__(
        self,
        __items: t.Mapping[K, V] | t.Iterable[tuple[K, V]] = (),
        /,
        **kwargs: V,
    ):
        super().__init__()

        self._items = dict(__items, **kwargs)

    def __setitem__(self, key: K, value: V, /) -> None:
        self._items[key] = value
        self._mark_as_changed()

    def __delitem__(self, key: K, /) -> None:
        del self._items[key]
        self._mark_as_changed()

    def __getitem__(self, key: K, /) -> V:
        self._mark_as_accessed()
        return self._items[key]

    def __iter__(self) -> t.Iterator[K]:
        self._mark_as_accessed()
        return iter(self._items)

    def __len__(self) -> int:
        self._mark_as_accessed()
        return len(self._items)

    def __contains__(self, key: object, /) -> bool:
        self._mark_as_accessed()
        return key in self._items

    def popitem(self) -> tuple[K, V]:
        self._mark_as_accessed()

        item = self._items.popitem()
        self._mark_as_changed()

        return item

    # These function signatures are a PITA. Screw the boilerplate, just inherit
    # the signature
    if not t.TYPE_CHECKING:

        def update(self, *args, **kwargs) -> None:
            self._items.update(*args, **kwargs)
            self._mark_as_changed()

        def pop(self, *args, **kwargs):
            self._mark_as_accessed()

            value = self._items.pop(*args, **kwargs)
            self._mark_as_changed()

            return value


class Set(ObservableContainer, collections.abc.MutableSet[T]):
    def __init__(self, items: t.Iterable[T] = (), /):
        super().__init__()

        self._items = set(items)

    def __iter__(self) -> t.Iterator[T]:
        self._mark_as_accessed()
        return iter(self._items)

    def __len__(self) -> int:
        self._mark_as_accessed()
        return len(self._items)

    def __contains__(self, value: object) -> bool:
        self._mark_as_accessed()
        return value in self._items

    def add(self, value: T) -> None:
        self._items.add(value)
        self._mark_as_changed()

    def update(self, values: t.Iterable[T]) -> None:
        self._items.update(values)
        self._mark_as_changed()

    def discard(self, value: T) -> None:
        self._items.discard(value)
        self._mark_as_changed()

    def clear(self) -> None:
        self._items.clear()
        self._mark_as_changed()
