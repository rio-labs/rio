from __future__ import annotations

from dataclasses import field

# <additional-imports>
from datetime import datetime, timezone

import openai  # type: ignore (hidden from user)

import rio

from .. import components as comps
from .. import conversation

# </additional-imports>


# <component>
@rio.page(
    name="Chat",
    url_segment="",
)
class ChatPage(rio.Component):
    """
    This is the only page in the entire app. It displays the chat history, a
    text input for the user to ask questions, and a placeholder if there is no
    chat history yet.
    """

    # Stores the conversation history.
    #
    # Since Python's dataclasses don't allow for mutable default values, we need
    # to use a factory function to create a new instance of the conversation
    # class.
    conversation: conversation.Conversation = field(
        default_factory=conversation.Conversation
    )

    # This will be used for the text input to store its result in
    user_message_text: str = ""

    # If this is `True`, the app is currently generating a response. An
    # indicator will be displayed to the user, and the text input will be
    # disabled.
    is_loading: bool = False

    async def on_text_input_confirm(self, *_) -> None:
        """
        Called when the text input is confirmed, or the "send" button pressed.
        The function ensures that the input isn't empty. If that's the case the
        message is sent on to the `on_question` function.
        """
        # If the user hasn't typed anything, do nothing
        message_text = self.user_message_text.strip()

        if not message_text:
            return

        # Empty the text input so the user can type another message
        self.user_message_text = ""

        # A question was asked!
        await self.on_question(message_text)

    async def on_question(self, message_text: str) -> None:
        """
        Called whenever the user asks a question. The function adds the user's
        message to the chat history, generates a response, and adds that to the
        chat history as well.
        """
        # Add the user's message to the chat history
        self.conversation.messages.append(
            conversation.ChatMessage(
                role="user",
                timestamp=datetime.now(tz=timezone.utc),
                text=message_text,
            )
        )

        # Indicate to the user that the app is doing something
        self.is_loading = True
        self.force_refresh()

        # Generate a response
        try:
            await self.conversation.respond(
                client=self.session[openai.AsyncOpenAI],
            )

        # Don't get stuck in loading state if an error occurs
        finally:
            self.is_loading = False

    def build(self) -> rio.Component:
        # If there aren't any messages yet, display a placeholder
        if not self.conversation.messages:
            return comps.EmptyChatPlaceholder(
                user_message_text=self.user_message_text,
                on_question=self.on_question,
                align_x=0.5,
                align_y=0.5,
            )

        # Center the chat on wide screens
        if self.session.window_width > 40:
            column_width = 40
            column_align_x = 0.5
        else:
            column_width = 0
            column_align_x = None

        # Prepare the message components
        message_components: list[rio.Component] = [
            comps.ChatMessage(msg) for msg in self.conversation.messages
        ]

        if self.is_loading:
            message_components.append(
                comps.GeneratingResponsePlaceholder(
                    align_x=0.5,
                )
            )

        # Combine everything into a neat package
        return rio.Stack(
            rio.Icon(
                "rio/logo:fill",
                min_width=3,
                min_height=3,
                align_x=0,
                margin=2,
                align_y=0,
            ),
            rio.Icon(
                "material/twinkle",
                min_width=3,
                min_height=3,
                align_x=1,
                margin=2,
                align_y=0,
            ),
            rio.Column(
                # Messages
                rio.ScrollContainer(
                    rio.Column(
                        # Display the messages
                        *message_components,
                        # Take up superfluous space
                        rio.Spacer(),
                        spacing=1,
                        # Center the column on wide screens
                        margin=2,
                        min_width=column_width,
                        align_x=column_align_x,
                    ),
                    grow_y=True,
                    scroll_x="never",
                ),
                # User input
                rio.Row(
                    rio.MultiLineTextInput(
                        label="Ask something...",
                        text=self.bind().user_message_text,
                        on_confirm=self.on_text_input_confirm,
                        is_sensitive=not self.is_loading,
                        grow_x=True,
                        min_height=8,
                    ),
                    rio.IconButton(
                        icon="material/navigate_next",
                        min_size=4,
                        on_press=self.on_text_input_confirm,
                        is_sensitive=not self.is_loading,
                        align_y=0.5,
                    ),
                    spacing=1,
                    min_width=column_width,
                    margin_bottom=1,
                    align_x=column_align_x,
                ),
                spacing=0.5,
            ),
        )


# </component>
