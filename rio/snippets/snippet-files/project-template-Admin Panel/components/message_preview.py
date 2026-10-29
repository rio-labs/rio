from __future__ import annotations

import rio

# <additional-imports>
from .. import data_models, theme

# </additional-imports>


# <component>
class MessagePreview(rio.Component):
    """
    Displays a preview of an email.

    This component is designed to show a brief summary of an email, including
    key details such as the sender, subject, and a snippet of the email body. It
    provides an interactive interface where users can click or tap on the
    preview to open the full email.

    ## Attributes:

    `email`: The email to display in the preview

    `on_press`: The event handler to call when the email is pressed
    """

    email: data_models.Email
    on_press: rio.EventHandler[[]] = None

    async def _on_press(self, _: rio.PointerEvent) -> None:
        # Rio has a built-in convenience function for calling event handlers.
        # This function will prevent your code from crashing if something
        # happens in the event handler, and also allows for the handler to be
        await self.call_event_handler(self.on_press)

    def build(self) -> rio.Component:
        # Define the text styles for the email preview
        if self.email.unread:
            text_style_header = rio.TextStyle(
                font_size=0.9,
                fill=theme.TEXT_FILL_BRIGHTER,
                font_weight="bold",
            )

            text_style_date = rio.TextStyle(
                font_size=0.95,
                fill=theme.TEXT_FILL_BRIGHTER,
                font_weight="bold",
            )

        else:
            text_style_header = rio.TextStyle(
                font_size=0.9,
            )

            text_style_date = rio.TextStyle(
                font_size=0.95,
                fill=self.session.theme.text_style.fill,
            )

        # Create the content of the email preview
        sender_row = rio.Row(spacing=0.5, align_x=0)
        sender_row.add(
            rio.Text(
                self.email.sender,
                style=text_style_header,
                align_x=0,
                align_y=0.5,
            )
        )

        # Add a small colored rectangle to indicate that the email is unread
        if self.email.unread:
            sender_row.add(
                rio.Rectangle(
                    fill=self.session.theme.primary_color,
                    corner_radius=99999,
                    align_x=0,
                    align_y=0.5,
                    min_height=0.5,
                    min_width=0.5,
                )
            )

        # Combine the sender and subject of the email
        content = rio.Column(
            rio.Row(
                rio.Column(
                    sender_row,
                    rio.Text(
                        self.email.subject,
                        style=text_style_header,
                        align_x=1,
                    ),
                    spacing=0.5,
                    align_x=0,
                    align_y=0.5,
                ),
                rio.Text(
                    self.email.sent_at.strftime("%b %d"),
                    style=text_style_date,
                    align_y=0,
                    align_x=1,
                ),
            ),
            rio.Text(
                self.email.body,
                style=theme.TEXT_STYLE_DARKER_SMALL,
                overflow="ellipsize",
            ),
            spacing=0.5,
            margin=1,
        )

        return rio.PointerEventListener(
            rio.Rectangle(
                content=rio.Column(
                    content,
                    rio.Separator(color=self.session.theme.neutral_color),
                ),
                fill=self.session.theme.background_color,
                hover_fill=self.session.theme.primary_color.replace(
                    opacity=0.1
                ),
                transition_time=0.1,
            ),
            on_press=self._on_press,
        )


# </component>
