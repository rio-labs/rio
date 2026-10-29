from __future__ import annotations

import rio

# <additional-imports>
from .. import components as comps
from .. import constants, data_models, theme

# </additional-imports>


# <component>
class NotificationCard(rio.Component):
    """
    A component that represents a notification card.

    This component displays a notification with details such as an image, title,
    message, and timestamp. It dynamically adjusts its layout based on the
    presence or absence of an image.

    ## Attributes

    `notification`: The notification object containing details such as image,
    title, message, and timestamp.
    """

    notification: data_models.Notification

    def build(self) -> rio.Component:
        # Create the image component based on the notification type
        # and whether an image is provided.
        if self.notification.image == "":
            image = rio.Rectangle(
                content=rio.Text(
                    "BN",
                    font_weight="bold",
                    font_size=1.1,
                    fill=theme.TEXT_FILL_DARKER,
                    align_x=0.5,
                    align_y=0.5,
                ),
                fill=self.session.theme.neutral_color,
                min_width=2.5,
                min_height=2.5,
                corner_radius=9999,
                align_y=0.5,
                stroke_width=0.1,
                stroke_color=theme.TEXT_FILL_DARKER,
            )

        # Add a red dot to the image
        elif self.notification.type == "sent you a message":
            image = rio.Stack(
                rio.Rectangle(
                    fill=rio.ImageFill(
                        self.session.assets / self.notification.image
                    ),
                    min_width=2.5,
                    min_height=2.5,
                    corner_radius=9999,
                ),
                rio.Rectangle(
                    fill=rio.Color.RED,
                    align_x=0.98,
                    align_y=0.05,
                    min_width=0.8,
                    min_height=0.8,
                    stroke_width=0.15,
                    stroke_color=self.session.theme.background_color,
                    corner_radius=9999,
                ),
                align_y=0.5,
            )
        # Add the user's image
        else:
            image = rio.Rectangle(
                fill=rio.ImageFill(
                    self.session.assets / self.notification.image
                ),
                min_width=2.5,
                min_height=2.5,
                corner_radius=9999,
                align_y=0.5,
            )

        # Create the notification card layout
        return rio.Rectangle(
            content=rio.Row(
                image,
                rio.Column(
                    rio.Text(
                        self.notification.name,
                        style=theme.TEXT_STYLE_SMALL_BOLD,
                    ),
                    rio.Text(
                        self.notification.type,
                        style=theme.TEXT_STYLE_DARKER_SMALL,
                    ),
                ),
                rio.Spacer(),
                rio.Text(
                    self.notification.created_at,
                    font_size=0.8,
                    fill=theme.TEXT_FILL_DARKER,
                    align_y=0,
                ),
                margin=0.5,
                spacing=0.5,
            ),
            fill=self.session.theme.background_color,
            hover_fill=self.session.theme.neutral_color,
            corner_radius=self.session.theme.corner_radius_small,
            transition_time=0.1,
            cursor="pointer",
        )


class NotificationButton(rio.Component):
    """
    A component that represents a button for displaying notifications.

    This component provides an interactive button that, when clicked, opens a
    dialog displaying a list of notifications. The dialog content is dynamically
    created using Rio components.
    """

    async def _create_dialog(self) -> None:
        # This function will be called to create the dialog's content.
        # It builds up a UI using Rio components, just like a regular
        # `build` function would.
        def build_dialog_content() -> rio.Component:
            # Build the dialog
            notifications = rio.Column()
            for notification in constants.NOTIFICATIONS:
                notifications.add(NotificationCard(notification))

            return rio.Rectangle(
                content=rio.Column(
                    rio.Row(
                        rio.Text(
                            "Notifications",
                            font_weight="bold",
                            selectable=False,
                        ),
                        rio.PointerEventListener(
                            rio.Rectangle(
                                content=rio.Icon("material/close", margin=0.5),
                                fill=self.session.theme.background_color,
                                hover_fill=self.session.theme.neutral_color,
                                corner_radius=self.session.theme.corner_radius_small,
                                transition_time=0.1,
                                cursor="pointer",
                                align_x=0.5,
                                align_y=0.5,
                            ),
                            align_x=1,
                            align_y=0,
                            on_press=on_close,
                        ),
                    ),
                    rio.Separator(
                        color=self.session.theme.neutral_color, margin_y=1
                    ),
                    rio.ScrollContainer(
                        notifications,
                        grow_y=True,
                    ),
                    margin=1,
                ),
                stroke_width=0.1,
                stroke_color=self.session.theme.neutral_color,
                fill=self.session.theme.background_color,
                align_x=1,
                min_width=25,
            )

        async def on_close(_: rio.PointerEvent) -> None:
            # This function will be called whenever the user selects an
            # Item. It simply closes the dialog with the selected value.
            await dialog.close()

        # Show the dialog
        dialog = await self.session.show_custom_dialog(
            build=build_dialog_content,
            # Prevent the user from interacting with the rest of the app
            # while the dialog is open
            modal=True,
            # Don't close the dialog if the user clicks outside of it
            user_closable=True,
            style="custom",
        )

        # Wait for the user to select an option
        result = await dialog.wait_for_close()

        # Return the selected value
        return result

    async def on_spawn_dialog(self, _: rio.PointerEvent) -> None:
        # Show a dialog and wait for the user to make a choice
        value = await self._create_dialog()

        # Store the value, but only if one was selected. If the dialog
        # gets closed without a selection, `value` will be `None`.
        if value is not None:
            self.value = value

    def build(self) -> rio.Component:
        # Create a notification button with a red dot and an icon
        content = rio.Stack(
            rio.Icon(
                "material/notifications",
                margin=0.5,
            ),
            rio.Rectangle(
                fill=rio.Color.RED,
                corner_radius=9999,
                align_x=0.7,
                align_y=0.25,
                min_width=0.7,
                min_height=0.7,
                stroke_width=0.15,
                stroke_color=self.session.theme.background_color,
            ),
        )
        return rio.PointerEventListener(
            rio.Rectangle(
                content=content,
                fill=rio.Color.TRANSPARENT,
                hover_fill=self.session.theme.neutral_color,
                corner_radius=self.session.theme.corner_radius_small,
                transition_time=0.1,
                cursor="pointer",
            ),
            on_press=self.on_spawn_dialog,
        )


class HomeSection(rio.Component):
    """
    This module defines components for the home section of the application.

    It includes components such as `NotificationCard` for displaying individual
    notifications and `NotificationButton` for interacting with and viewing a
    list of notifications.


    ## Attributes

    `_is_open`: A boolean indicating whether the popup is open or closed.
    """

    _is_open: bool = False

    def on_press(self) -> None:
        self._is_open = not self._is_open

    def on_press_new_email(self) -> None:
        self.session.navigate_to("/inbox")

    def on_press_new_user(self) -> None:
        self.session.navigate_to("/settings/members")

    def build(self) -> rio.Component:
        # Create the content for the popup
        content_new = comps.PopupRectangle(
            rio.Column(
                comps.StyledRectangle(
                    "New Email",
                    "material/send",
                    on_press=self.on_press_new_email,
                ),
                comps.StyledRectangle(
                    "New User",
                    "material/person_add",
                    on_press=self.on_press_new_user,
                ),
                margin=theme.POPUP_INNER_MARGIN,
            ),
        )

        # Create the bar of the home section
        return rio.Column(
            rio.Separator(color=self.session.theme.neutral_color),
            rio.Row(
                rio.Text(
                    "Home",
                    font_weight="bold",
                    align_x=0,
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Tooltip(
                    NotificationButton(),
                    tip=rio.Text(
                        "Notifications", style=theme.TOOLTIP_TEXTSTYLE
                    ),
                ),
                rio.Popup(
                    anchor=rio.IconButton(
                        "material/add",
                        color=self.session.theme.primary_color,
                        on_press=self.on_press,
                        min_size=2.2,
                    ),
                    content=content_new,
                    is_open=self.bind()._is_open,
                    position="bottom",
                ),
                spacing=1,
                margin_y=0.8,
                margin_x=1,
            ),
            rio.Separator(color=self.session.theme.neutral_color),
            align_y=0,
        )


# </component>
