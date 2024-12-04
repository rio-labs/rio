from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
@rio.page(
    name="Home",
    url_segment="",
)
class LandingPage(rio.Component):
    """
    The landing page of the website.

    This page features the main content of the website, including the hero
    section, services of our fictional company, cards, testimonials, and a 'Get
    Started' call-to-action section.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for desktop devices.
        """
        return rio.Column(
            comps.HeroSection(),
            comps.ServicePower(),
            comps.ServiceSpeed(),
            comps.CardSection(),
            comps.Testimonials(),
            comps.GetStarted(),
            spacing=14,  # Space between components for better readability on desktop
            align_x=0.5,  # Center horizontally
            align_y=0,  # Align to the top vertically
            min_width=80,  # Fixed width to ensure proper layout on larger screens
            margin_bottom=10,  # Space below the column
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.
        """
        return rio.Column(
            comps.HeroSection(),
            comps.ServicePower(),
            comps.ServiceSpeed(),
            comps.CardSection(),
            comps.Testimonials(),
            comps.GetStarted(),
            spacing=7,  # Reduced space to accommodate smaller screens
            margin=1,  # Minimal margin for compact layout
        )

    def build(self) -> rio.Component:
        """
        Construct and return the page layout based on the user's device type.

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
