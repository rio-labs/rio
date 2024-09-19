from __future__ import annotations

# <additional-imports>
from datetime import datetime, timezone
from typing import *  # type: ignore

import rio

from .. import data_models, persistence

# </additional-imports>


# <component>
class Navbar(rio.Component):
    """
    A navbar with a fixed position and responsive width.
    """

    # Make sure the navbar will be rebuilt when the app navigates to a different
    # page. While Rio automatically detects state changes and rebuilds
    # components as needed, navigating to other pages is not considered a state
    # change, since it's not stored in the component.
    #
    # Instead, we can use Rio's `on_page_change` event to trigger a rebuild of
    # the navbar when the page changes.
    @rio.event.on_page_change
    async def on_page_change(self) -> None:
        # Rio comes with a function specifically for this. Whenever Rio is
        # unable to detect a change automatically, use this function to force a
        # refresh.
        await self.force_refresh()

    async def on_logout(self) -> None:
        user_session = self.session[data_models.UserSession]

        # Expire the session
        pers = self.session[persistence.Persistence]

        await pers.update_session_duration(
            user_session,
            new_valid_until=datetime.now(tz=timezone.utc),
        )

        # Detach everything from the session. This informs all components that
        # nobody is logged in.
        self.session.detach(data_models.AppUser)
        self.session.detach(data_models.UserSession)

        # Navigate to the login page, since login page is our root page we need to navigate
        # to "/" as the root page
        self.session.navigate_to("/")

    def build(self) -> rio.Component:
        try:
            # Which page is currently active? This will be used to highlight the
            # correct navigation button.
            #
            # `active_page_instances` contains the same `rio.Page` instances that
            # you've passed the app during creation. Since multiple pages can be
            # active at a time (e.g. /foo/bar/baz), this is a list.
            active_page = self.session.active_page_instances[1]
            active_page_url_segment = active_page.url_segment
        except IndexError:
            # Handle the case where there are no active pages. e.g. when the user is
            # not logged in.
            active_page_url_segment = None
            # You might want to log this or handle it in another way
            # For example, you could set a default value or raise a custom exception
            # logging.warning("No active page instances found.")

        # Check if the user is logged in and display the appropriate buttons based on
        # the user's status
        try:
            self.session[data_models.AppUser]
            user_settings = True
        except KeyError:
            user_settings = False

        # The navbar should appear above all other components. This is easily
        # done by using a `rio.Overlay` component.
        return rio.Overlay(
            # Use a rectangle for visual separation
            rio.Rectangle(
                content=rio.Row(
                    # Links can be used to navigate to other pages and
                    # external URLs. You can pass either a simple string, or
                    # another component as their content.
                    rio.Link(
                        rio.IconButton(
                            "rio/logo",
                            style="plain-text",
                            min_size=2.5,
                        ),
                        "/app/home",
                    ),
                    # This spacer will take up any superfluous space,
                    # effectively pushing the subsequent buttons to the
                    # right.
                    rio.Spacer(),
                    # By sticking buttons into a `rio.Link`, we can easily
                    # make the buttons navigate to other pages, without
                    # having to write an event handler. Notice how there is
                    # no Python function called when the button is clicked.
                    # Check if user is logged in and display the appropriate
                    # buttons
                    *(
                        # Display the navbar buttons if the user is logged in
                        [
                            rio.Link(
                                rio.Button(
                                    "Home",
                                    icon="material/news",
                                    style=(
                                        "major"
                                        if active_page_url_segment == "home"
                                        else "plain-text"
                                    ),
                                ),
                                "/app/home",
                            ),
                            rio.Link(
                                rio.Button(
                                    "News",
                                    icon="material/news",
                                    style=(
                                        "major"
                                        if active_page_url_segment
                                        == "news-page"
                                        else "plain-text"
                                    ),
                                ),
                                "/app/news-page",
                            ),
                            # Same game, different button
                            rio.Link(
                                rio.Button(
                                    "About",
                                    icon="material/info",
                                    style=(
                                        "major"
                                        if active_page_url_segment
                                        == "about-page"
                                        else "plain-text"
                                    ),
                                ),
                                "/app/about-page",
                            ),
                            # Logout
                            rio.Button(
                                "Logout",
                                icon="material/logout",
                                style="plain-text",
                                on_press=self.on_logout,
                            ),
                        ]
                        if user_settings
                        # Display the login button if the user is not logged in
                        else [
                            rio.Link(
                                rio.Button(
                                    "Login",
                                    icon="material/login",
                                    style="plain-text",
                                ),
                                "/",
                            ),
                        ]
                    ),
                    spacing=1,
                    margin=1,
                ),
                # Set the fill of the rectangle to the neutral color of the theme and
                # Add a corner radius
                fill=self.session.theme.neutral_color,
                corner_radius=self.session.theme.corner_radius_medium,
                # Add shadow properties
                shadow_radius=0.8,
                shadow_color=self.session.theme.shadow_color,
                shadow_offset_y=0.2,
                # Overlay assigns the entire screen to its child component.
                # Since the navbar isn't supposed to take up all space, assign
                # an alignment.
                align_y=0,
                margin_x=5,
                margin_y=2,
            ),
        )


# </component>
