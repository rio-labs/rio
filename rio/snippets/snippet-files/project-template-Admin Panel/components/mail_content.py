import rio

# <additional-imports>
from .. import data_models, theme

# </additional-imports>


# <component>
class MailContent(rio.Component):
    """
    The content of an email. Displays the email's sender, subject, body, and
    provides a text input for replying to the email.

    This component is designed to show the full content of a selected email,
    including the sender's profile image, name, subject, and body. It also
    includes a text input field for the user to compose a reply.


    ## Attributes:

    `selected_email`: The currently selected email
    """

    selected_email: data_models.Email

    def build(self) -> rio.Component:
        # Create the email header row
        email_header_content = rio.Row(
            # Add the sender's profile image as a circular avatar
            rio.Rectangle(
                fill=rio.ImageFill(
                    self.session.assets / self.selected_email.sender_image
                ),
                corner_radius=9999,
                transition_time=0,
                min_width=3.5,
                min_height=3.5,
                align_x=0,
                align_y=0.5,
            ),
            # Add the sender's name and email subject in a vertical column
            rio.Column(
                rio.Text(
                    self.selected_email.sender,
                    fill=theme.TEXT_FILL_BRIGHTER,
                    font_weight="bold",
                ),
                rio.Text(
                    self.selected_email.subject,
                ),
                align_y=0,
                spacing=0.5,
            ),
            # Add a spacer to push the timestamp to the right
            rio.Spacer(),
            # Add the email's sent date as a timestamp
            rio.Text(
                str(self.selected_email.sent_at.strftime("%d %b")),
                fill=theme.TEXT_FILL_BRIGHTER,
                font_weight="bold",
                align_y=0,
            ),
            spacing=1,
        )

        return rio.Column(
            email_header_content,
            rio.Separator(color=self.session.theme.neutral_color, margin_y=1.5),
            rio.Text(
                self.selected_email.body,
                overflow="wrap",
                font_size=1.2,
            ),
            rio.Spacer(),
            rio.Separator(color=self.session.theme.neutral_color, margin_y=1),
            rio.MultiLineTextInput(
                "Reply",
                min_height=10,
            ),
            margin=1,
        )


# </component>
