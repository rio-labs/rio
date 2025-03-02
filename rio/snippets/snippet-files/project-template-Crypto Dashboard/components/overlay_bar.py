import rio

# <additional-imports>
from .. import components as comps

# </additional-imports>


# <component>
class OverlayBar(rio.Component):
    """
    A component that represents the overlay bar at the top of the dashboard.

    The OverlayBar contains:
    - A "Dashboard" title.
    - A notification button.
    - A user profile image or placeholder.
    - Frosted glass styling for the background with customizable opacity and blur.

    """

    _page_name: str = "Dashboard"

    @rio.event.on_page_change
    def get_page_name(self) -> None:
        """
        Get the name of the active page and set it as the page name.
        """
        if self.session.active_page_url.name == "":
            self._page_name = "Dashboard"
            self.force_refresh()

        else:
            self._page_name = self.session.active_page_url.name.capitalize()
            self.force_refresh()

    def build(self) -> rio.Component:
        # Build the overlay bar layout
        return rio.Overlay(
            rio.Rectangle(
                # Row layout to arrange items horizontally
                content=rio.Row(
                    rio.Text(self._page_name, font_size=2, font_weight="bold"),
                    rio.Spacer(),  # Spacer to push items to the right
                    # Add notification button component
                    comps.NotificationButton(),
                    # Add user profile image
                    rio.Rectangle(
                        fill=rio.ImageFill(
                            self.session.assets / "testimonial.png"
                        ),
                        min_width=2.5,
                        min_height=2.5,
                        align_y=0.5,
                        align_x=0,
                        corner_radius=self.session.theme.corner_radius_small,
                    ),
                    spacing=2,
                    margin_right=2 + self.session.scroll_bar_size,
                ),
                fill=rio.FrostedGlassFill(
                    self.session.theme.background_color.replace(opacity=0.7),
                    blur_size=0.6,
                ),
                align_y=0,
                min_height=5,
                margin_left=14,
            ),
        )


# </component>
