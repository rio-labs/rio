# <additional-imports>
import functools
import typing as t

import rio

from .. import components as comps
from .. import constants, data_models

# </additional-imports>


# <component>
@rio.page(
    name="Inbox",
    url_segment="inbox",
)
class InboxPage(rio.Component):
    """
    The inbox page of the email client. Displays a list of emails and a preview
    of the selected email.


    ## Attributes:

    `switcher_option`: The selected value of the switcher bar

    `selected_email`: The email that is currently selected
    """

    switcher_option: t.Literal["All", "Unread"] = "All"
    selected_email: data_models.Email | None = None

    def on_press(self, email: data_models.Email) -> None:
        self.selected_email = email

    def build(self) -> rio.Component:
        # Filter emails based on the selected switcher option
        if self.switcher_option == "All":
            emails_to_show = constants.EMAILS
        else:
            emails_to_show = [
                email for email in constants.EMAILS if email.unread
            ]

        # Create a list of email preview components
        email_content = rio.Column()

        for email in emails_to_show:
            email_content.add(
                comps.MessagePreview(
                    email=email,
                    on_press=functools.partial(self.on_press, email),
                )
            )

        # Push up content
        email_content.add(
            rio.Spacer(),
        )

        return rio.Row(
            rio.Column(
                comps.InboxHeader(switcher_option=self.bind().switcher_option),
                rio.ScrollContainer(
                    email_content,
                    grow_y=True,
                ),
            ),
            rio.Column(
                comps.InboxEmail(selected_email=self.selected_email),
                grow_x=True,
            ),
        )


# </component>
