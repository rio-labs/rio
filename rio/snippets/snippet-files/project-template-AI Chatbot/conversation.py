import dataclasses
import typing as t
from datetime import datetime, timezone

import openai  # type: ignore (hidden from user)


@dataclasses.dataclass
class ChatMessage:
    """
    A simple storage class containing all the information needed for a single
    chat message.
    """

    role: t.Literal["user", "assistant"]
    timestamp: datetime
    text: str


@dataclasses.dataclass
class Conversation:
    """
    The start of the show. This class contains a list of messages and can
    connect to OpenAI to generate smart responses to the user's messages.
    """

    # The entire message history
    messages: list[ChatMessage] = dataclasses.field(default_factory=list)

    async def respond(self, client: openai.AsyncOpenAI) -> ChatMessage:
        """
        Creates an AI generated response for this conversation and appends it
        to the messages list. Also returns the new message.

        ## Raises

        `ValueError` if the most recent message is not by the user.
        """

        # Make sure the last message was by the user
        if not self.messages or self.messages[-1].role != "user":
            raise ValueError("The most recent message must be by the user")

        # Convert all messages to the format needed by the API
        api_messages: list[t.Any] = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Format your response in markdown, for example by using **bold**, and _italic_ amongst others.",
            }
        ] + [
            {
                "role": message.role,
                "content": message.text,
            }
            for message in self.messages
        ]

        # Generate a response
        api_response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=api_messages,
            max_tokens=500,
        )

        assert isinstance(api_response.choices[0].message.content, str)

        response = ChatMessage(
            role="assistant",
            timestamp=datetime.now(tz=timezone.utc),
            text=api_response.choices[0].message.content,
        )

        # Append the message and return it as well
        self.messages.append(response)

        return response
