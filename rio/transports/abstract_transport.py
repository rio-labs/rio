import abc
import asyncio

__all__ = [
    "AbstractTransport",
    "TransportClosed",
    "TransportClosedIntentionally",
    "TransportInterrupted",
]


class AbstractTransport(abc.ABC):
    """
    Represents a communication channel between a `Session` and the client.
    """

    def __init__(self) -> None:
        self.closed_event = asyncio.Event()

    @property
    def is_closed(self) -> bool:
        return self.closed_event.is_set()

    @abc.abstractmethod
    async def send_if_possible(self, message: str, /) -> None:
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
    async def close(self) -> None:
        """
        Close the connection. Set `self.closed` when finished.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        cls_name = type(self).__name__
        status = "closed" if self.is_closed else "open"
        return f"<{cls_name} {status} @{hex(id(self))}>"


class TransportClosed(Exception):
    pass


class TransportClosedIntentionally(TransportClosed):
    pass


class TransportInterrupted(TransportClosed):
    pass
