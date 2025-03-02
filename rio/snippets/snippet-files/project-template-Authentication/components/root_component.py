from __future__ import annotations

import rio

from .. import components as comps


# <component>
class RootComponent(rio.Component):
    """
    This component will be used as the root for the app. This means that it will
    always be visible, regardless of which page is currently active.

    This makes it the perfect place to put components that should be visible on
    all pages, such as a navbar or a footer.

    Additionally, the root will contain a `rio.PageView`. Page views don't have
    any appearance of their own, but they are used to display the content of the
    currently active page. Thus, we'll always see the navbar and footer, with
    the content of the current page sandwiched in between.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            # The navbar contains a `rio.Overlay`, so it will always be on top
            # of all other components.
            comps.Navbar(),
            # The page view will display the content of the current page.
            rio.PageView(
                # Make sure the page view takes up all available space. Without
                # this the navbar would be assigned the same space as the page
                # content.
                grow_y=True,
            ),
        )


# </component>
