from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
NAV_BUTTON_DATA_MOBILE: list[tuple[str, str]] = [
    ("Home", ""),
    ("Pricing", "pricing"),
    ("Blog", "blog"),
]


class HamburgerButton(rio.Component):
    """
    A toggleable hamburger button component.

    This component displays a hamburger menu icon when the menu is closed and a
    close icon when the menu is open. It allows toggling the `is_open` state
    through a pointer (click/touch) event.


    ## Attributes:

    `is_open`: Indicates whether the menu is currently open or closed.
    """

    is_open: bool = False

    def _on_toggle_open(self, _: rio.PointerEvent) -> None:
        """
        Handles the toggle action when the button is pressed.

        This method toggles the `is_open` state between `True` and `False`.
        """
        self.is_open = not self.is_open

    def build(self) -> rio.Component:
        """
        Builds the hamburger button component.

        The button dynamically changes its icon and appearance based on the
        `is_open` state.
        """
        # Determine the icon and fill color based on the open state
        if self.is_open:
            # Display a close icon when the menu is open
            icon = "material/close"
            fill = self.session.theme.text_style.fill
        else:
            # Display a hamburger menu icon when closed
            icon = "material/menu"
            fill = self.session.theme.text_style.fill

        # Ensure the fill is a valid rio.Color instance
        assert isinstance(fill, rio.Color)

        return rio.PointerEventListener(
            rio.Rectangle(
                content=rio.Icon(
                    icon=icon,
                    fill=fill,
                    min_width=2.2,
                    min_height=2.2,
                ),
                fill=rio.Color.TRANSPARENT,
                # Show pointer cursor on hover
                cursor="pointer",
            ),
            on_press=self._on_toggle_open,
        )


class Navbar(rio.Component):
    """
    A responsive and fixed-position navigation bar with separate layouts for
    desktop and mobile devices.


    ## Attributes:

    `is_open`: Whether the mobile navigation menu is open.
    """

    is_open: bool = False

    # Make sure the navbar will be rebuilt when the app navigates to a different
    # page. While Rio automatically detects state changes and rebuilds
    # components as needed, navigating to other pages is not considered a state
    # change, since it's not stored in the component.
    #
    # Instead, we can use Rio's `on_page_change` event to trigger a rebuild of
    # the navbar when the page changes.
    @rio.event.on_page_change
    def on_page_change(self) -> None:
        """
        Trigger a rebuild of the navbar when the page changes.
        """
        # Rio comes with a function specifically for this. Whenever Rio is
        # unable to detect a change automatically, use this function to force a
        # refresh.
        self.force_refresh()

    def _get_active_url_fragment(self) -> str | None:
        """
        Get the active URL fragment to determine the currently selected page.
        """

        # Prepare the URL
        segments = self.session.active_page_url.parts

        # Special case: Not deep enough
        if len(segments) <= 1:
            return None

        # Special case: Home page
        if segments[1] == "":
            return ""

        # Regular case: use the url segment of the active page
        return segments[1]

    def _on_switcherbar_value_change(
        self, event: rio.SwitcherBarChangeEvent
    ) -> None:
        """
        Handles changes to the SwitcherBar value.

        Navigates to the corresponding page and closes the mobile menu.
        """
        # Prepare the URL
        if event.value is None:
            target_segment = self._get_active_url_fragment()
        else:
            target_segment = event.value

        # Navigate to the target page
        self.session.navigate_to(f"/{target_segment}")
        # Close the mobile menu
        self.is_open = False

    def _desktop_build(self) -> rio.Component:
        """
        Build the desktop layout.
        """
        # Which page is currently active? This will be used to highlight the
        # correct navigation button.
        #
        # `active_page_instances` contains `rio.ComponentPage` instances that
        # that are created during app creation. Since multiple pages can be
        # active at a time (e.g. /foo/bar/baz), this is a list rather than just
        # a single page.
        active_page = self.session.active_page_instances[0]
        active_page_url_segment = active_page.url_segment

        # Determine styling based on theme (light or dark)
        if self.session.theme.is_light_theme:
            fine_border_line_fill_color = self.session.theme.primary_color
            frosted_glass_fill_color = (
                self.session.theme.background_color.replace(opacity=0.7)
            )

        else:
            fine_border_line_fill_color = self.session.theme.neutral_color
            frosted_glass_fill_color = (
                self.session.theme.background_color.replace(opacity=0.7)
            )

        # The navbar should appear above all other components. This is easily
        # done by using a `rio.Overlay` component.
        return rio.Overlay(
            rio.Column(
                # The navbar consists of a rectangle with a row of buttons inside.
                rio.Rectangle(
                    content=rio.Row(
                        rio.Spacer(),
                        rio.Row(
                            # By sticking buttons into a `rio.Link`, we can easily
                            # make the buttons navigate to other pages, without
                            # having to write an event handler. Notice how there is
                            # no Python function called when the button is clicked.
                            rio.Link(
                                rio.IconButton(
                                    "rio/logo",
                                    style="plain-text",
                                    min_size=2.5,
                                ),
                                "/",
                            ),
                            rio.Spacer(),
                            # Same game different button
                            rio.Link(
                                rio.Button(
                                    "Pricing",
                                    style=(
                                        "colored-text"
                                        if active_page_url_segment == "pricing"
                                        else "plain-text"
                                    ),
                                ),
                                "/pricing",
                            ),
                            # Same game, different button
                            rio.Link(
                                rio.Button(
                                    "Blog",
                                    style=(
                                        "colored-text"
                                        if active_page_url_segment == "blog"
                                        else "plain-text"
                                    ),
                                ),
                                "/blog",
                            ),
                            # Same game, different button
                            comps.OutlinedNeutralButton(text="Sign in"),
                            # Same game, different button
                            rio.Link(
                                content=rio.Button(
                                    rio.Row(
                                        rio.Text(
                                            "Sign up",
                                            fill=self.session.theme.background_color,
                                        ),
                                        rio.Icon("material/arrow_forward"),
                                        align_x=0.5,
                                        spacing=1,
                                        margin_x=1,
                                    ),
                                    color=rio.Color.from_hex("ffffff"),
                                ),
                                target_url="/",  # TODO: Change this to the correct URL
                            ),
                            spacing=1,
                            margin_y=1,
                            min_width=80,
                            align_x=0.5,
                        ),
                        rio.Spacer(),
                    ),
                    # Set the fill of the rectangle to the neutral color of the theme and
                    # add a FrostedGlassFill
                    fill=rio.FrostedGlassFill(
                        frosted_glass_fill_color,
                        blur_size=0.6,
                    ),
                    min_height=4.5,
                    align_y=0,
                ),
                # Add a thin line to separate the navbar from the rest of the content
                # This line will be placed below the rectangle
                rio.Rectangle(
                    fill=fine_border_line_fill_color,
                    min_height=0.1,
                    align_y=0,
                ),
                spacing=0,
                align_y=0,
            ),
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the mobile layout.
        """
        active_url_fragment = self.session.active_page_url.name

        # Determine styling based on theme (light or dark)
        if self.session.theme.is_light_theme:
            fine_border_line_fill_color = self.session.theme.primary_color
            frosted_glass_fill_color = (
                self.session.theme.background_color.replace(opacity=0.7)
            )

        else:
            fine_border_line_fill_color = self.session.theme.neutral_color
            frosted_glass_fill_color = (
                self.session.theme.background_color.replace(opacity=0.7)
            )

        # Add the mobile navigation menu when open
        if self.is_open:
            # Add the local navigation buttons
            primary_column = rio.Rectangle(
                content=rio.SwitcherBar(
                    names=[option[0] for option in NAV_BUTTON_DATA_MOBILE],
                    values=[option[1] for option in NAV_BUTTON_DATA_MOBILE],
                    selected_value=active_url_fragment,
                    allow_none=True,
                    color="primary",
                    orientation="vertical",
                    on_change=self._on_switcherbar_value_change,
                    margin=0.5,
                    align_y=0,
                ),
                fill=self.session.theme.neutral_color,
                corner_radius=(
                    0,
                    0,
                    self.session.theme.corner_radius_large,
                    self.session.theme.corner_radius_large,
                ),
                shadow_radius=1,
                margin_bottom=1,
            )

        else:
            primary_column = None

        # The navbar should appear above all other components. This is easily
        # done by using a `rio.Overlay` component.
        return rio.Overlay(
            rio.Column(
                rio.Rectangle(
                    content=rio.Row(
                        rio.Link(
                            rio.IconButton(
                                "rio/logo",
                                style="plain-text",
                                min_size=2.5,
                            ),
                            "/",
                        ),
                        rio.Spacer(),
                        comps.OutlinedNeutralButton(
                            text="Sign in",
                            align_y=0.5,
                        ),
                        HamburgerButton(is_open=self.bind().is_open),
                        spacing=1.1,
                        margin_x=0.6,
                        margin_left=1.2,
                        margin_right=1.2,
                    ),
                    # Set the fill of the rectangle to the neutral color of the theme and
                    # add a FrostedGlassFill
                    fill=rio.FrostedGlassFill(
                        frosted_glass_fill_color,
                        blur_size=0.6,
                    ),
                    align_y=0,
                    min_height=4,  # Fixed height of the navbar
                ),
                # Add a thin line to separate the navbar from the rest of the content
                # This line will be placed below the rectangle
                rio.Rectangle(
                    fill=fine_border_line_fill_color,
                    min_height=0.1,
                    align_y=0,
                ),
                rio.Switcher(content=primary_column),
                align_y=0,
            ),
        )

    def build(self) -> rio.Component:
        """
        Build and return the page layout based on the user's device type.

        Determines whether the user is on a desktop or mobile device and builds
        the corresponding layout.
        """
        device = self.session[data_models.PageLayout].device

        if device == "desktop":
            # Build and return the desktop-optimized layout
            return self._desktop_build()

        else:
            # Build and return the mobile-optimized layout
            return self._mobile_build()


# </component>
