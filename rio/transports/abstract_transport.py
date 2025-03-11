import abc
import asyncio

__all__ = [
    "AbstractTransport",
    "TransportClosedIntentionally",
    "TransportInterrupted",
]


class AbstractTransport(abc.ABC):
    """
    Represents a communication channel between a `Session` and the client.
    """

    def __init__(self) -> None:
        self.closed = asyncio.Event()

    @abc.abstractmethod
    async def send(self, message: str, /) -> None:
        """
        Send the message if possible. If the transport is closed, do nothing.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def receive(self) -> str:
        """
        Return the next message received from the client. If the transport is
        closed, throw either `TransportInterrupted` or
        `TransportClosedIntentionally`.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """
        Close the connection. Set `self.closed` when finished.
        """
        raise NotImplementedError


class TransportClosedIntentionally(Exception):
    pass


class TransportInterrupted(Exception):
    pass
