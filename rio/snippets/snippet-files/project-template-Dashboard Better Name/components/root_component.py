from __future__ import annotations

import rio

# <additional-imports>
from .. import components as comps

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
    of the currently active page. Thus, we'll always see the navbar and footer,
    with the content of the current page in between.
    """

    is_open: bool = False

    # TODO: add keypress
    def open_search(self, ev: rio.KeyPressEvent) -> None:
        """
        This method will be called when the user clicks the search icon in the
        navbar. It will open the search overlay.
        """
        print(f"Key pressed: {ev}")
        if str(ev) == "control + k":
            print("Opening search overlay")
            self.is_open = not self.is_open

    def build(self) -> rio.Component:
        return rio.Row(
            # The navbar contains a `rio.Overlay`, so it will always be on top
            # of all other components.
            comps.SideBar(),
            # Add some empty space so the navbar doesn't cover the content.
            # The page view will display the content of the current page.
            rio.PageView(
                # Make sure the page view takes up all available space.
                grow_y=True,
                grow_x=True,
            ),
        )

        # return rio.KeyEventListener(
        #     rio.Popup(
        #         anchor=rio.Row(
        #             # The navbar contains a `rio.Overlay`, so it will always be on top
        #             # of all other components.
        #             comps.SideBar(),
        #             # Add some empty space so the navbar doesn't cover the content.
        #             # The page view will display the content of the current page.
        #             rio.PageView(
        #                 # Make sure the page view takes up all available space.
        #                 grow_y=True,
        #                 grow_x=True,
        #             ),
        #         ),
        #         content=rio.KeyEventListener(
        #             rio.Card(
        #                 content=rio.Text("Search overlay"),
        #                 align_x=0.5,
        #                 align_y=0.5,
        #                 min_height=30,
        #                 min_width=60,
        #             ),
        #             on_key_press=self.open_search,
        #         ),
        #         position="fullscreen",
        #         is_open=self.bind().is_open,
        #     ),
        #     # Listen for the `s` key to open the search overlay.
        #     on_key_press=self.open_search,
        # )


# </component>
