from .abstract_transport import AbstractTransport, TransportClosed

__all__ = ["MultiTransport"]


class MultiTransport(AbstractTransport):
    """
    Sends outgoing messages to multiple transports.
    """

    def __init__(
        self,
        main_transport: AbstractTransport,
        *extra_transports: AbstractTransport,
    ) -> None:
        super().__init__()

        assert not main_transport.is_closed

        self._main_transport = main_transport
        self._extra_transports = extra_transports

    async def send_if_possible(self, message: str, /) -> None:
        await self._main_transport.send_if_possible(message)

        for transport in self._extra_transports:
            await transport.send_if_possible(message)

        if self._main_transport.is_closed:
            await self.close()

    async def receive(self) -> str:
        try:
            return await self._main_transport.receive()
        except TransportClosed:
            await self.close()
            raise

    async def close(self) -> None:
        await self._main_transport.close()

        for transport in self._extra_transports:
            await transport.close()

        self.closed_event.set()
