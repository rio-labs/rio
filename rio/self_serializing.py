from __future__ import annotations

import abc

from uniserde import Jsonable

import rio

__all__ = ["SelfSerializing"]


class SelfSerializing(abc.ABC):
    """
    Properties with types that inherit from `SelfSerializing` will be serialized
    when sent to the client.
    """

    @abc.abstractmethod
    def _serialize(self, sess: rio.Session) -> Jsonable:
        raise NotImplementedError
