import abc
import asyncio

from uniserde import JsonDoc

__all__ = [
    "AbstractTransport",
    "TransportClosedIntentionally",
    "TransportInterrupted",
]


class AbstractTransport(abc.ABC):
    def __init__(self) -> None:
        self.closed = asyncio.Event()

    @abc.abstractmethod
    async def send(self, message: str, /) -> None:
        """
        Send the message if possible. If the transport is closed, do nothing.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def receive(self) -> JsonDoc:
        """
        Return the next message received from the client. If the transport is
        closed, throw either `TransportInterrupted` or
        `TransportClosedIntentionally`.
        """
        raise NotImplementedError

    def close(self) -> None:
        self.closed.set()
        self._close()

    @abc.abstractmethod
    def _close(self) -> None:
        """
        Close the connection.
        """
        raise NotImplementedError


class TransportClosedIntentionally(Exception):
    pass


class TransportInterrupted(Exception):
    pass
