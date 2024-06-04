import abc

from uniserde import JsonDoc

__all__ = [
    "AbstractTransport",
    "TransportClosedIntentionally",
    "TransportInterrupted",
]


class AbstractTransport(abc.ABC):
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

    @abc.abstractmethod
    async def close(self) -> None:
        """
        Close the connection.
        """
        raise NotImplementedError


class TransportClosedIntentionally(Exception):
    pass


class TransportInterrupted(Exception):
    pass
