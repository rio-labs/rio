from __future__ import annotations

import typing as t

import rio

# <additional-imports>
from .. import components as comps
from .. import constants, data_models, theme

# </additional-imports>


# <component>
class RioLogo(rio.Component):
    """
    A component that represents the Rio logo.
    """

    def build(self) -> rio.Component:
        return rio.Row(
            rio.Icon(
                "rio/logo",
                min_height=1.2,
                min_width=1.2,
            ),
            rio.Text(
                "Rio",
                selectable=False,
                style=theme.TEXT_STYLE_SMALL_BOLD,
            ),
            spacing=0.2,
            align_x=0,
        )


class Section(rio.Component):
    """
    A component that represents a section in the sidebar.

    This component displays a clickable section with a name and an optional
    target URL. When clicked, it navigates to the specified URL and refreshes
    the component.


    ## Attributes

    `section_name`: The name of the section to be displayed.

    `target_url`: The URL to navigate to when the section is clicked.

    `_is_active`: Indicates whether the section is currently active.
    """

    section_name: str
    target_url: str | None = None

    _is_active: bool = False

    def on_press(self, _: rio.PointerEvent) -> None:
        """
        When clicked, it navigates to the specified URL and refreshes
        the component
        """
        assert self.target_url is not None
        self.session.navigate_to(self.target_url)
        self.force_refresh()

    def build(self) -> rio.Component:
        # Set the fill and hover fill colors based on the active state
        if self._is_active:
            fill = self.session.theme.neutral_color.brighter(0.04)
            hover_fill = self.session.theme.neutral_color.brighter(0.04)
            rectangle_fill = theme.TEXT_FILL_BRIGHTER
            text_style = rio.TextStyle(
                font_size=0.9, fill=theme.TEXT_FILL_BRIGHTER
            )

        else:
            fill = rio.Color.TRANSPARENT
            hover_fill = self.session.theme.neutral_color
            rectangle_fill = theme.TEXT_FILL_DARKER
            text_style = theme.TEXT_STYLE_DARKER_SMALL

        return rio.PointerEventListener(
            content=rio.Rectangle(
                content=rio.Row(
                    rio.Rectangle(
                        fill=rectangle_fill,
                        hover_fill=hover_fill,
                        corner_radius=9999,
                        align_x=0.5,
                        align_y=0.5,
                        min_height=0.4,
                        min_width=0.4,
                    ),
                    rio.Text(self.section_name, style=text_style),
                    margin=0.5,
                    margin_left=0.5 + 0.45,
                    spacing=0.5,
                    align_x=0,
                ),
                fill=fill,
                hover_fill=hover_fill,
                cursor="pointer",
                transition_time=0.1,
                corner_radius=self.session.theme.corner_radius_small,
            ),
            on_press=self.on_press,
        )


class MajorSection(rio.Component):
    """
    A component that represents a major section in the sidebar.

    This component displays a major section with a title, an icon, and a list of
    subsections. It allows navigation to a target URL when clicked and manages
    its active and open states.


    ## Attributes

    `title`: The title of the major section.

    `icon`: The icon representing the major section.

    `target_url`: The URL to navigate to when the major section is clicked.

    `active_main_section`: The identifier for the currently active main section.

    `active_section`: The identifier for the currently active subsection.

    `sections`: A list of subsections under the major section.

    `is_active`: Indicates whether the major section is currently active.
    `is_open`: Indicates whether the major section is currently open.
    """

    title: str
    icon: str
    target_url: str
    active_main_section: str
    active_section: str
    sections: list[data_models.Section]

    is_active: bool = False
    _is_open: bool = False

    def on_press(self, _: rio.PointerEvent) -> None:
        """
        When clicked, it navigates to the specified URL and refreshes
        the component
        """
        self.session.navigate_to(self.target_url)
        self.force_refresh()

    def on_toggle(self, _: rio.PointerEvent) -> None:
        # Toggle the open state of the major section
        self._is_open = not self._is_open

    def build(self) -> rio.Component:
        # Set the fill and hover fill colors based on the active state
        if self.is_active:
            fill = self.session.theme.neutral_color.brighter(0.04)
            hover_fill = self.session.theme.neutral_color.brighter(0.04)
            text_style = rio.TextStyle(
                font_size=0.9, fill=theme.TEXT_FILL_BRIGHTER
            )
            icon_fill = theme.TEXT_FILL_BRIGHTER

        else:
            fill = rio.Color.TRANSPARENT
            hover_fill = self.session.theme.neutral_color
            text_style = theme.TEXT_STYLE_DARKER_SMALL
            icon_fill = theme.TEXT_FILL_DARKER

        # Create the content for the major section if there are no subsections
        if self.sections == []:
            content = rio.Row(
                rio.Icon(
                    self.icon,
                    fill=icon_fill,
                    min_height=1.2,
                    min_width=1.2,
                ),
                rio.Text(
                    self.title,
                    selectable=False,
                    style=text_style,
                ),
                spacing=1,
                align_x=0,
                margin=0.5,
            )

        # Create the content for the major section if there are subsections
        else:
            content = rio.Row(
                rio.Icon(
                    self.icon,
                    fill=icon_fill,
                    min_height=1.2,
                    min_width=1.2,
                ),
                rio.Text(
                    self.title,
                    selectable=False,
                    style=text_style,
                ),
                rio.Spacer(),
                rio.Icon(
                    (
                        "material/keyboard_arrow_down"
                        if self._is_open
                        else "material/chevron_right"
                    ),
                    fill=icon_fill,
                    align_x=1,
                    min_height=1.2,
                    min_width=1.2,
                ),
                spacing=1,
                margin=0.5,
            )

            # Create the content for the subsections
            if self._is_open:
                content_column = rio.Column(spacing=0.2, margin_top=0.5)
                # Add sections to the content column
                for section in self.sections:
                    content_column.add(
                        Section(
                            section_name=section.section_name,
                            target_url=section.target_url,
                            _is_active=(
                                section.section_name == self.active_section
                            ),
                        )
                    )
                # Construct the content for the rio.Switcher, including a small
                # vertical line (rectangle) to the left of the switcher.
                content_switcher = rio.Stack(
                    content_column,
                    rio.Rectangle(
                        fill=theme.TEXT_FILL_DARKER,
                        min_width=0.05,
                        align_x=0,
                        margin_left=0.71 + 0.4,
                        margin_y=0.3,
                        margin_top=0.8,
                    ),
                )
            # If the major section is not open, set content_switcher to None so
            # nothing is displayed.
            else:
                content_switcher = None

        # If there are no subsections, create a themed rectangle as the Major
        # Section
        if self.sections == []:
            return rio.PointerEventListener(
                rio.Rectangle(
                    content=content,
                    fill=fill,
                    hover_fill=hover_fill,
                    cursor="pointer",
                    transition_time=0.1,
                    corner_radius=self.session.theme.corner_radius_small,
                ),
                on_press=self.on_press,
            )
        # If there are subsections, create a themed rectangle as the Major
        # Section with a switcher for the subsections.
        else:
            return rio.Column(
                rio.PointerEventListener(
                    rio.Rectangle(
                        content=content,
                        fill=fill,
                        hover_fill=hover_fill,
                        cursor="pointer",
                        transition_time=0.1,
                        corner_radius=self.session.theme.corner_radius_small,
                    ),
                    on_press=self.on_toggle,
                ),
                rio.Switcher(content=content_switcher, transition_time=0.2),
            )


class UserAvatar(rio.Component):
    """
    A component that represents a user avatar with a popup menu.

    This component displays a user's avatar and provides an interactive popup
    menu with options such as navigating to the settings page. The popup can be
    toggled open or closed.


    ## Attributes:

    `user`: The user object containing details about the user.

    `is_open`: Indicates whether the popup menu is currently open.
    """

    user: data_models.User

    _is_open: bool = False

    def on_toggle_popup(self) -> None:
        self._is_open = not self._is_open

    def _on_press_settings(self) -> None:
        """
        Navigate to the settings page and close the popup.
        """
        # TODO: just use a rio.Link instead?
        self.session.navigate_to("/settings/general")
        self._is_open = False

    def on_toggle(self, _: rio.PointerEvent) -> None:
        self._is_open = not self._is_open

    def build(self) -> rio.Component:
        # Create the content for the user avatar
        content_user = rio.Row(
            # Create the user avatar with a circular shape
            rio.Rectangle(
                fill=rio.ImageFill(self.session.assets / self.user.image),
                min_height=1.4,
                min_width=1.4,
                corner_radius=9999,
            ),
            rio.Text(
                self.user.name,
                selectable=False,
                font_size=0.9,
                font_weight="bold",
                fill=theme.TEXT_FILL_BRIGHTER,
            ),
            # Push the icon to the right
            rio.Spacer(),
            rio.Icon(
                "material/more_vert",
                fill=theme.TEXT_FILL_BRIGHTER,
            ),
            spacing=0.5,
            margin=0.5,
        )

        # Create the content for the popup menu
        content_popup = comps.PopupRectangle(
            rio.Column(
                rio.Text(
                    "Signed in as",
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                    margin_x=0.5,
                    margin_top=0.5,
                    margin_bottom=0.2,
                ),
                rio.Text(
                    self.user.email,
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                    font_weight="bold",
                    margin_x=0.5,
                    margin_bottom=0.5,
                ),
                rio.Separator(
                    color=self.session.theme.neutral_color.brighter(0.2),
                    margin_y=theme.POPUP_INNER_MARGIN,
                ),
                comps.StyledRectangle(
                    text="Settings",
                    icon="material/settings",
                    on_press=self._on_press_settings,
                ),
                comps.StyledRectangle(
                    text="Command menu",
                    icon="material/keyboard_command_key",
                    on_press=self.on_toggle_popup,
                ),
                rio.Link(
                    comps.StyledRectangle(
                        text="Help & Support",
                        icon="material/help",
                    ),
                    target_url="https://discord.com/invite/7ejXaPwhyH",
                    open_in_new_tab=True,
                ),
                rio.Separator(
                    color=self.session.theme.neutral_color.brighter(0.2),
                    margin_y=theme.POPUP_INNER_MARGIN,
                ),
                rio.Link(
                    comps.StyledRectangle(
                        text="Documentation",
                        icon="material/import_contacts",
                    ),
                    target_url="https://rio.dev/docs",
                    open_in_new_tab=True,
                ),
                rio.Link(
                    comps.StyledRectangle(
                        text="Github repository",
                        icon="brand/github",
                    ),
                    target_url="https://github.com/rio-labs/rio",
                    open_in_new_tab=True,
                ),
                rio.Separator(
                    color=self.session.theme.neutral_color.brighter(0.2),
                    margin_y=theme.POPUP_INNER_MARGIN,
                ),
                comps.StyledRectangle(
                    text="Logout",
                    icon="material/logout",
                    on_press=self.on_toggle_popup,
                ),
                margin=theme.POPUP_INNER_MARGIN,
            ),
            align_x=0,
            min_width=13.5,
        )

        return rio.Popup(
            anchor=rio.PointerEventListener(
                rio.Rectangle(
                    content=content_user,
                    fill=rio.Color.TRANSPARENT,
                    hover_fill=self.session.theme.neutral_color,
                    corner_radius=self.session.theme.corner_radius_small,
                    transition_time=0.1,
                    cursor="pointer",
                ),
                on_press=self.on_toggle,
            ),
            content=content_popup,
            position="top",
            is_open=self.bind()._is_open,
            user_closable=True,
        )


class SideBar(rio.Component):
    """ """

    @rio.event.on_page_change
    def _on_page_change(self) -> None:
        self.force_refresh()

    def _get_current_section(self) -> t.Tuple[str, str]:
        """
        Get the current section of the active page URL for a two-level section structure.
        """
        active_page_url = str(self.session.active_page_url.path or "")

        # Traverse through MAJOR_SECTIONS
        for main_section in constants.MAJOR_SECTIONS:
            if main_section.target_url == active_page_url:
                # Match found at the main section level
                return ("", main_section.main_section_name)

            if main_section.sections:  # sections is now a list
                for section in main_section.sections:
                    if section.target_url == active_page_url:
                        # Match found at the subsection level
                        return (
                            section.section_name,
                            main_section.main_section_name,
                        )

        # Default return value if no match is found
        return ("", "")

    def build(self) -> rio.Component:
        # Get the current section and main section
        active_section, active_main_section = self._get_current_section()

        # Create the content for the sidebar and add content
        content = rio.Column(
            margin=1,
            spacing=0.2,
        )

        content.add(
            RioLogo(
                margin_left=0.5,
                align_x=0,
            ),
        )
        content.add(
            rio.Spacer(min_height=2, grow_y=False),
        )

        # Add the predefined major sections to the sidebar
        for main_section in constants.MAJOR_SECTIONS:
            content.add(
                MajorSection(
                    main_section.main_section_name,
                    main_section.icon,
                    target_url=main_section.target_url,
                    active_main_section=active_main_section,
                    active_section=active_section,
                    sections=main_section.sections,
                    is_active=(
                        main_section.main_section_name == active_main_section
                    ),
                )
            )

        # Push the following content to the bottom of the sidebar
        content.add(
            rio.Spacer(),
        )

        content.add(
            MajorSection(
                title="Invite people",
                icon="material/add",
                target_url="/settings/members",
                active_main_section=active_main_section,
                active_section=active_section,
                sections=[],
                is_active="Invite people" == active_main_section,
            ),
        )

        content.add(
            MajorSection(
                title="Help & Support",
                icon="material/help",
                target_url="/https://discord.com/invite/7ejXaPwhyH",
                active_main_section=active_main_section,
                active_section=active_section,
                sections=[],
                is_active="Invite people" == active_main_section,
            ),
        )

        content.add(
            rio.Separator(
                color=self.session.theme.neutral_color,
                margin_y=0.5,
            )
        )

        content.add(UserAvatar(constants.USER))

        # Return the sidebar as a themed rectangle
        return rio.Rectangle(
            content=content,
            fill=self.session.theme.background_color,
            stroke_color=self.session.theme.neutral_color,
            stroke_width=0.1,
            min_width=15.5,
        )


# </component>
