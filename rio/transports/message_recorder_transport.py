import asyncio
import json
import typing as t

import typing_extensions as te
from uniserde import JsonDoc

from . import abstract_transport

__all__ = ["MessageRecorderTransport"]


class MessageRecorderTransport(abstract_transport.AbstractTransport):
    def __init__(
        self, *, process_sent_message: t.Callable[[JsonDoc], None] | None = None
    ) -> None:
        super().__init__()

        self.process_sent_message = process_sent_message

        self.sent_messages = list[JsonDoc]()
        self._responses = asyncio.Queue[
            JsonDoc
            | type[abstract_transport.TransportInterrupted]
            | type[abstract_transport.TransportClosedIntentionally]
        ]()

    @te.override
    async def send_if_possible(self, msg: str) -> None:
        parsed_msg = json.loads(msg)
        self.sent_messages.append(parsed_msg)

        if self.process_sent_message is not None:
            self.process_sent_message(parsed_msg)

    @te.override
    async def receive(self) -> str:
        response = await self._responses.get()

        if isinstance(response, type) and issubclass(response, Exception):
            raise response()

        return json.dumps(response)

    async def close(self) -> None:
        self._responses.put_nowait(
            abstract_transport.TransportClosedIntentionally
        )
        self.closed_event.set()

    def queue_response(
        self,
        response: JsonDoc
        | type[abstract_transport.TransportInterrupted]
        | type[abstract_transport.TransportClosedIntentionally],
    ) -> None:
        self._responses.put_nowait(response)
