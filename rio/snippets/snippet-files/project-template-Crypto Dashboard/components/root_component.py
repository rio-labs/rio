from __future__ import annotations

import rio

# <additional-imports>
from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
class RootComponent(rio.Component):
    """
    This page will be used as the root component for the app. This means, that
    it will always be visible, regardless of which page is currently active.

    This makes it the perfect place to put components that should be visible on
    all pages, such as a navbar or a footer.

    Additionally, the root page will contain a `rio.PageView`. Page views don't
    have any appearance on their own, but they are used to display the content
    of the currently active page. Thus, we'll always see the Sidebar with the
    content of the current page next to it.
    """

    def desktop_build(self) -> rio.Component:
        return rio.Row(
            # The Sidebar contains a `rio.Overlay`, so it will always be on top
            # of all other components.
            comps.NavBar(),
            # The page view will display the content of the current page.
            rio.Column(
                comps.OverlayBar(),
                rio.PageView(
                    # Make sure the page view takes up all available space.
                    grow_y=True,
                ),
                # Make sure the page view takes up all available space.
                grow_x=True,
            ),
        )

    def mobile_build(self) -> rio.Component:
        return rio.Column(
            # The Sidebar contains a `rio.Overlay`, so it will always be on top
            # of all other components.
            comps.NavBar(),
            # Add a spacer at the top of the page view to ensure the content
            # isn't obscured by the Navbar.
            rio.Spacer(min_height=5, grow_y=False),
            # The page view will display the content of the current page.
            rio.PageView(
                # Make sure the page view takes up all available space.
                grow_y=True,
                grow_x=True,
                margin_x=0.5,
            ),
            margin_bottom=1,
        )

    def build(self) -> rio.Component:
        device = self.session[data_models.PageLayout].device

        if device == "desktop":
            return self.desktop_build()

        return self.mobile_build()


# </component>
