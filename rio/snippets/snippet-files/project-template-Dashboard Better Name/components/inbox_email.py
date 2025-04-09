import rio

# <additional-imports>
from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class TooltipIconButton(rio.Component):
    """
    A button with an icon and a tooltip.


    ## Attributes:

    `icon:` icon which will be displayed on the button.

    `tip:` tooltip text which will be displayed when the button is hovered.
    """

    icon: str
    tip: str

    def build(self) -> rio.Component:
        return rio.Tooltip(
            anchor=rio.Rectangle(
                content=rio.Icon(self.icon, margin=0.5),
                hover_fill=self.session.theme.neutral_color,
                corner_radius=self.session.theme.corner_radius_small,
                transition_time=0.1,
                cursor="pointer",
                align_x=0.5,
                align_y=0.5,
            ),
            tip=rio.Text(
                self.tip,
                style=theme.TOOLTIP_TEXTSTYLE,
            ),
            position="bottom",
        )


class MailInfoPopupButton(rio.Component):
    """
    A box with an icon which will be used to toggle a popup.


    ## Attributes:

    `icon:` icon which will be displayed.

    `is_open:` boolean value which will be used to toggle the popup.
    """

    icon: str
    is_open: bool

    def on_toggle_popup(self, _: rio.PointerEvent) -> None:
        self.is_open = not self.is_open

    def build(self) -> rio.Component:
        return rio.PointerEventListener(
            rio.Rectangle(
                content=rio.Icon(self.icon, margin=0.5),
                fill=self.session.theme.background_color,
                hover_fill=self.session.theme.neutral_color,
                corner_radius=self.session.theme.corner_radius_small,
                transition_time=0.1,
                cursor="pointer",
                align_x=0.5,
                align_y=0.5,
            ),
            on_press=self.on_toggle_popup,
        )


class MailInfoPopupContent(rio.Component):
    """
    Content with options for the email.


    ## Attributes:

    `is_open:` boolean value which will be used to toggle the popup.
    """

    _is_open: bool = False

    def on_toggle_popup(self) -> None:
        self._is_open = not self._is_open

    def build(self) -> rio.Component:
        # Create a column with options for the email
        column_1 = rio.Column(
            comps.StyledRectangle(
                text="Mark as unread",
                icon="material/check_circle",
                on_press=self.on_toggle_popup,
            ),
            comps.StyledRectangle(
                text="Mark as important",
                icon="material/error",
                on_press=self.on_toggle_popup,
            ),
        )
        column_2 = rio.Column(
            comps.StyledRectangle(
                text="Star thread",
                icon="material/star",
                on_press=self.on_toggle_popup,
            ),
            comps.StyledRectangle(
                text="Mute thread",
                icon="material/pause_circle",
                on_press=self.on_toggle_popup,
            ),
        )

        return comps.PopupRectangle(
            content=rio.Column(
                column_1,
                rio.Separator(
                    color=self.session.theme.neutral_color.brighter(0.2),
                    margin_y=theme.POPUP_INNER_MARGIN,
                ),
                column_2,
                margin=theme.POPUP_INNER_MARGIN,
            ),
        )


class InboxEmailHeader(rio.Component):
    """
    A header for the email.

    This component represents the header section of an email, providing various
    action buttons such as archive, move to junk, snooze, reply, and forward. It
    also includes a popup menu for additional actions.

    ## Attributes:

    `_is_open`: boolean value which will be used to toggle the popup.
    """

    _is_open: bool = False

    def on_toggle_popup(self) -> None:
        self._is_open = not self._is_open

    def build(self) -> rio.Component:
        return comps.StrokeRectangle(
            content=rio.Row(
                TooltipIconButton(icon="material/move_to_inbox", tip="Archive"),
                TooltipIconButton(icon="material/outbox", tip="Move to junk"),
                rio.Separator(color=self.session.theme.neutral_color),
                TooltipIconButton(icon="material/schedule", tip="Snooze"),
                rio.Spacer(),
                TooltipIconButton(icon="material/reply", tip="Reply"),
                TooltipIconButton(icon="material/forward", tip="Forward"),
                rio.Separator(color=self.session.theme.neutral_color),
                rio.Popup(
                    anchor=MailInfoPopupButton(
                        icon="material/more_vert", is_open=self.bind()._is_open
                    ),
                    content=MailInfoPopupContent(_is_open=self.bind()._is_open),
                    position="bottom",
                    is_open=self.bind()._is_open,
                    user_closable=True,
                ),
                spacing=0.5,
                margin_x=1,
                margin_y=0.5,
            ),
            corner_radius=0,
            min_height=4,
            align_y=0,
        )


class InboxEmail(rio.Component):
    """
    A component that displays an email.

    This component is responsible for rendering the content of an email. If no
    email is selected, it displays a placeholder icon. If an email is selected,
    it displays the email's header and content.


    ## Attributes:

    `selected_email`: The email that will be displayed.
    """

    selected_email: data_models.Email | None

    def no_email_selected_build(self) -> rio.Component:
        # Display a placeholder rectangle with a mail icon when no email is
        # selected
        return comps.StrokeRectangle(
            content=rio.Icon(
                "material/mail",
                fill=theme.TEXT_FILL_DARKER,
                align_y=0.5,
                align_x=0.5,
                min_height=6,
                min_width=6,
            ),
            corner_radius=0,
        )

    def email_selected_build(self) -> rio.Component:
        # Ensure an email is selected
        assert self.selected_email is not None

        return rio.Column(
            InboxEmailHeader(align_y=0),
            comps.MailContent(selected_email=self.selected_email, grow_y=True),
        )

    def build(self) -> rio.Component:
        # Check if an email is selected and return the corresponding UI
        if self.selected_email is None:
            return self.no_email_selected_build()
        else:
            return self.email_selected_build()


# </component>
