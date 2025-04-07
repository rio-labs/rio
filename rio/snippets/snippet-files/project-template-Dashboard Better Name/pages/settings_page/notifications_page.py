import rio

# <additional-imports>
from ... import components as comps
from ... import data_models, theme

# </additional-imports>


# <component>
NOTIFICATION_SETTINGS = [
    data_models.NotificationSetting(
        heading="Email",
        sub_heading="Receive a daily email digest.",
    ),
    data_models.NotificationSetting(
        heading="Desktop",
        sub_heading="Receive desktop notifications.",
    ),
]

ACCOUNT_SETTINGS = [
    data_models.NotificationSetting(
        heading="Weekly digest",
        sub_heading="Receive a weekly digest of news.",
    ),
    data_models.NotificationSetting(
        heading="Product updates",
        sub_heading="Receive a monthly email with all new features and updates.",
    ),
    data_models.NotificationSetting(
        heading="Important updates",
        sub_heading="Receive emails about important updates like security fixes, maintenance, etc.",
    ),
]


@rio.page(
    name="Notifications",
    url_segment="notifications",
)
class GeneralPage(rio.Component):
    """
    Represents the Notifications page of the application.

    This page allows users to manage their notification preferences. It is
    divided into two sections:

    1. Notification channels: Settings for where notifications are sent (e.g.,
       email, desktop).

    2. Account updates: Settings for receiving updates about the application.

    """

    def build(self) -> rio.Component:
        # Add all notification groups
        content_notifications = rio.Column(margin=1)

        for setting in NOTIFICATION_SETTINGS:
            content_notifications.add(
                comps.ToggleGroup(
                    heading=setting.heading,
                    sub_heading=setting.sub_heading,
                )
            )

            # Add separator after each item except the last one
            if setting != NOTIFICATION_SETTINGS[-1]:
                content_notifications.add(
                    rio.Separator(
                        color=self.session.theme.neutral_color,
                        margin_y=1,
                    )
                )

        # Add all account groups
        content_account = rio.Column(margin=1)

        for setting in ACCOUNT_SETTINGS:
            content_account.add(
                comps.ToggleGroup(
                    heading=setting.heading,
                    sub_heading=setting.sub_heading,
                )
            )

            # Add separator after each item except the last one
            if setting != ACCOUNT_SETTINGS[-1]:
                content_account.add(
                    rio.Separator(
                        color=self.session.theme.neutral_color,
                        margin_y=1,
                    )
                )

        return rio.Column(
            rio.Row(
                rio.Column(
                    rio.Text(
                        "Notification channels",
                        font_weight="bold",
                    ),
                    rio.Text(
                        "Where can we notify you?",
                        style=theme.TEXT_STYLE_DARKER_SMALL,
                    ),
                    spacing=0.5,
                    align_y=0,
                ),
                comps.StrokeRectangle(content_notifications),
                proportions=[1.5, 2],
            ),
            rio.Separator(
                color=self.session.theme.neutral_color,
            ),
            rio.Row(
                rio.Column(
                    rio.Text(
                        "Account updates",
                        font_weight="bold",
                    ),
                    rio.Text(
                        "Receive updates about Rio.",
                        style=theme.TEXT_STYLE_DARKER_SMALL,
                    ),
                    spacing=0.5,
                    align_y=0,
                ),
                comps.StrokeRectangle(content_account),
                proportions=[1.5, 2],
            ),
            spacing=1.5,
            align_y=0,
        )


# </component>
