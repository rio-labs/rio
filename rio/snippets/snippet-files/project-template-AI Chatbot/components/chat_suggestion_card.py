from __future__ import annotations

import rio


# <component>
class ChatSuggestionCard(rio.Component):
    """
    While the chat is empty, a placeholder is displayed. That placeholder
    contains several of these components, which are suggestions for the user to
    start a conversation.
    """

    icon: str
    text: str

    on_press: rio.EventHandler[str] = None

    async def _on_press(self) -> None:
        await self.call_event_handler(self.on_press, self.text)

    def build(self) -> rio.Component:
        # A suggestion is just an icon, text and button wrapped inside a card.
        return rio.Card(
            rio.Column(
                rio.Icon(self.icon, min_width=1.8, min_height=1.8),
                rio.Text(
                    self.text,
                    justify="center",
                    overflow="wrap",
                    grow_y=True,
                    align_y=0.5,
                ),
                rio.Button(
                    "Ask",
                    icon="material/navigate_next",
                    style="minor",
                    on_press=self._on_press,
                ),
                spacing=0.6,
                margin=1,
            ),
        )


# </component>
