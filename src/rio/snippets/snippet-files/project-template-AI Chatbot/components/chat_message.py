from __future__ import annotations

from typing import *  # type: ignore

import rio

# <additional-imports>
from .. import conversation

# </additional-imports>


# <component>
class ChatMessage(rio.Component):
    """
    This component displays a single chat message, allowing you can create a
    message history by stacking multiple instances of this component vertically.
    """

    model: conversation.ChatMessage

    def build(self) -> rio.Component:
        # User messages look slightly different from the bot's responses. This
        # makes it easer for the user to distinguish between the two.
        if self.model.role == "user":
            icon = "rio/logo"
            color = "neutral"
        else:
            icon = "material/twinkle"
            color = "background"

        return rio.Row(
            # Display an icon on the left side of the message. It is wrapped
            # inside of a card to give it a circular shape.
            rio.Card(
                rio.Icon(
                    icon,
                    width=2,
                    height=2,
                    margin=0.8,
                ),
                # Using an enormous corner radius ensures that the card is fully
                # circular.
                corner_radius=99999,
                color="neutral",
                margin=0.5,
                align_y=0,
            ),
            # The message content is displayed inside of a second card. By using
            # markdown to show the message the user and chatbot can apply
            # formatting to their messages.
            rio.Card(
                rio.Markdown(
                    self.model.text,
                    margin=1.5,
                ),
                width="grow",
                color=color,
            ),
        )


# </component>
