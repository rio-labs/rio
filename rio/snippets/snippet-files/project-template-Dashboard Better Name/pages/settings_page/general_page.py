import typing as t

import rio

# <additional-imports>
from ... import components as comps

# </additional-imports>


# <component>
@rio.page(
    name="General Settings",
    url_segment="general",
)
class GeneralPage(rio.Component):
    """
    Represents the General Settings page of the application.

    This page allows users to customize various settings related to their
    account and profile. It includes options for theme customization, profile
    information, and account management.

    ## Attributes

    `theme_mode`: The current theme mode of the application. This can be either
    "Light" or "Dark".
    """

    theme_mode: t.Literal["Light", "Dark"] = "Dark"

    async def on_press(self) -> None:
        """
        Spawn a dialog to confirm the deletion of the user's account.
        """
        _ = await self.session.show_yes_no_dialog(
            title="Delete account",
            text="Are you sure you want to delete your account?",
            yes_text="Delete",
            no_text="Cancel",
            yes_color="danger",
            no_color=rio.Color.WHITE,
        )

    def build(self) -> rio.Component:
        content = rio.Column(spacing=1.5, align_y=0)

        content.add(
            comps.ContentContainer(
                "Theme",
                "Customize the look and feel of your dashboard.",
                content_right=comps.SingleSelectDropdown(
                    label=self.theme_mode,
                    options=["Light", "Dark"],
                    selected_value=self.bind().theme_mode,
                    align_x=1,
                    align_y=0.5,
                ),
            ),
        )

        content.add(
            comps.ContentContainer(
                "Profile",
                "This information will be displayed publicly so be careful what you share.",
                content_right=rio.Button(
                    "Save changes",
                    shape="rounded",
                    color=rio.Color.WHITE,
                    align_y=0.5,
                    align_x=1,
                ),
            ),
        )

        content.add(
            comps.ContentContainer(
                "Name",
                "Will appear on receipts, invoices, and other communication.",
                is_required=True,
                content_right=rio.TextInput(
                    "Chris Whatsoever",  # TODO: datamodel
                    align_y=0.5,
                    align_x=1,
                    min_width=30,
                ),
            ),
        )

        content.add(
            comps.ContentContainer(
                "Email",
                "Used to sign in, for email receipts and product updates.",
                is_required=True,
                content_right=rio.TextInput(
                    "chris@rio-labs.dev",  # TODO datamodel
                    align_y=0.5,
                    align_x=1,
                    min_width=30,
                ),
            ),
        )

        content.add(
            comps.ContentContainer(
                "Username",
                "Your unique username for logging in and your profile URL.",
                is_required=True,
                content_right=rio.TextInput(
                    "chrisOK",  # TODO datamodel
                    prefix_text="rio.dev/",
                    align_y=0.5,
                    align_x=1,
                    min_width=30,
                ),
            ),
        )
        content.add(
            comps.ContentContainer(
                "Account",
                "No longer want to use our service? You can delete your account here. This action is not reversible. All information related to this account will be deleted permanently.",
            ),
        )
        content.add(
            rio.Button(
                "Delete account",
                shape="rounded",
                color="danger",
                margin_top=2,
                align_x=0,
                align_y=0,
                on_press=self.on_press,
            ),
        )
        return content


# </component>
