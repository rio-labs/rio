import functools
import typing as t
import weakref

K = t.TypeVar("K")
V = t.TypeVar("V")


class WeakKeyIdDefaultDict(t.Generic[K, V]):
    """
    A dictionary-like object that uses the id() of weakly-referenced keys.
    When a key is garbage collected, its entry is automatically removed.
    Keys are compared by object identity, not equality.
    Requires a default_factory, like collections.defaultdict.
    """

    def __init__(
        self,
        default_factory: t.Callable[[], V],
    ) -> None:
        # Maps id(key) -> value
        self._values: dict[int, V] = {}

        # Maps id(key) -> weakref.ref(key)
        #
        # The weakref has a callback that removes the entry from both `_data`
        # and `_refs`.
        self._key_refs: dict[int, weakref.ref[K]] = {}

        # Factory for default values
        self._default_factory: t.Callable[[], V] = default_factory

    def _remove(self, key_id: int, ignored=None) -> None:
        """
        Remove the entry for the given key id from both _data and _refs. This is
        used as callback for `weakref.ref`.
        """
        self._values.pop(key_id, None)
        self._key_refs.pop(key_id, None)

    def __setitem__(self, key: K, value: V) -> None:
        """
        Associate the value with the key. The keys are identified by their `id`,
        not the actual Python object.
        """
        key_id = id(key)

        self._values[key_id] = value
        self._key_refs[key_id] = weakref.ref(
            key,
            functools.partial(self._remove, key_id),
        )

    def __getitem__(self, key: K) -> V:
        """
        Retrieve the value associated with the key. If the key is not present,
        create and store a default value using the factory. Raises KeyError only
        if the key was present but has been collected.
        """
        # This needs no check for whether the key is still alive, because it was
        # just passed into this function, so it must be.
        try:
            return self._values[id(key)]
        except KeyError:
            pass

        # If no value was found, create a default
        result = self._default_factory()
        self[key] = result
        return result

    def __delitem__(self, key: K) -> None:
        """
        Remove the entry for the key. Raises KeyError if not present.
        """
        # This needs no check for whether the key is still alive, because it was
        # just passed into this function, so it must be.
        key_id = id(key)

        try:
            del self._key_refs[key_id]
            del self._values[key_id]
        except KeyError:
            raise KeyError(key)

    def __len__(self) -> int:
        """
        Return the number of live entries in the dictionary.
        """
        return len(self._values)

    def __iter__(self) -> t.Iterator[K]:
        """
        Return an iterator over the keys of the dictionary.
        """
        # A value may technically die during iteration, causing it to be removed
        # from the dictionary, which would cause an error. Thus convert
        # everything to a list first.
        for key_ref in list(self._key_refs.values()):
            key = key_ref()

            # If it were `None`, it would have been removed from the dictionary
            assert key is not None

            yield key
