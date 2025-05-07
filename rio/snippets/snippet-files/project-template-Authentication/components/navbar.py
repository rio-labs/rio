from __future__ import annotations

# <additional-imports>
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
    def on_page_change(self) -> None:
        # Rio comes with a function specifically for this. Whenever Rio is
        # unable to detect a change automatically, use this function to force a
        # refresh.
        self.force_refresh()

    async def on_logout(self) -> None:
        user_session = self.session[data_models.UserSession]

        # Delete the session from the database
        pers = self.session[persistence.Persistence]
        await pers.delete_session(user_session.id)

        # Detach everything from the session. This informs all components that
        # nobody is logged in.
        self.session.detach(data_models.AppUser)
        self.session.detach(data_models.UserSession)

        # Navigate to the login page to prevent the user being on a page that is
        # prohibited without being logged in.
        self.session.navigate_to("/")

    def build(self) -> rio.Component:
        # Determine the layout based on the window width
        desktop_layout = self.session.window_width > 30

        try:
            # Which page is currently active? This will be used to highlight the
            # correct navigation button.
            #
            # `active_page_instances` contains `rio.ComponentPage` instances
            # that that are created during app creation. Since multiple pages
            # can be active at a time (e.g. /foo/bar/baz), this is a list rather
            # than just a single page.
            active_page = self.session.active_page_instances[1]
            active_page_url_segment = active_page.url_segment
        except IndexError:
            # Handle the case where there are no active sub-pages. e.g. when the
            # user is not logged in.
            active_page_url_segment = None

        # Check if the user is logged in and display the appropriate buttons
        # based on the user's status
        try:
            self.session[data_models.AppUser]

        # If no user is attached, nobody is logged in
        except KeyError:
            user_settings = False

        # If a user is attached, they are logged in
        else:
            user_settings = True

        # Create the content of the navbar. First we create a row with a certain
        # spacing and margin.  We can use the `.add()` method to add components
        # by condition to the row.
        navbar_content = rio.Row(spacing=1, margin=1)

        # Links can be used to navigate to other pages and
        # external URLs. You can pass either a simple string, or
        # another component as their content.
        navbar_content.add(
            rio.Link(
                rio.IconButton(
                    "rio/logo",
                    style="plain-text",
                    min_size=2.5,
                ),
                "/app/home",
            )
        )

        # This spacer will take up any superfluous space,
        # effectively pushing the subsequent buttons to the
        # right.
        navbar_content.add(rio.Spacer())

        # Based on the user's status, display the appropriate buttons
        if user_settings:
            # By sticking buttons into a `rio.Link`, we can easily
            # make the buttons navigate to other pages, without
            # having to write an event handler. Notice how there is
            # no Python function called when the button is clicked.
            navbar_content.add(
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
                )
            )

            # Same game, different button
            navbar_content.add(
                rio.Link(
                    rio.Button(
                        "News",
                        icon="material/news",
                        style=(
                            "major"
                            if active_page_url_segment == "news-page"
                            else "plain-text"
                        ),
                    ),
                    "/app/news-page",
                )
            )

            # Same game, different button
            navbar_content.add(
                rio.Link(
                    rio.Button(
                        "About",
                        icon="material/info",
                        style=(
                            "major"
                            if active_page_url_segment == "about-page"
                            else "plain-text"
                        ),
                    ),
                    "/app/about-page",
                )
            )

            # Logout
            navbar_content.add(
                rio.Button(
                    "Logout",
                    icon="material/logout",
                    style="plain-text",
                    on_press=self.on_logout,
                )
            )

        # Display the login button if the user is not logged in
        else:
            navbar_content.add(
                rio.Link(
                    rio.Button(
                        "Sign In",
                        icon="material/login",
                        style="plain-text",
                    ),
                    "/",
                )
            )

        # The navbar should appear above all other components. This is easily
        # done by using a `rio.Overlay` component.
        return rio.Overlay(
            # Use a rectangle for visual separation
            rio.Rectangle(
                # Use the content we've built up by conditions
                content=navbar_content,
                # Set the fill of the rectangle to the neutral color of the
                # theme
                fill=self.session.theme.neutral_color,
                # Round the corners
                corner_radius=self.session.theme.corner_radius_medium,
                # Add a shadow to make the navbar stand out above other content
                shadow_radius=0.8,
                shadow_color=self.session.theme.shadow_color,
                shadow_offset_y=0.2,
                # Overlay assigns the entire screen to its child component.
                # Since the navbar isn't supposed to take up all space, align
                # it.
                align_y=0,
                margin_x=2 if desktop_layout else 0.5,
                margin_y=2,
            ),
        )


# </component>
