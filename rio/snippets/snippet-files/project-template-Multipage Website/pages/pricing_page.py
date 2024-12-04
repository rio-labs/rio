# <additional-imports>
import rio

from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
@rio.page(
    name="Pricing",
    url_segment="pricing",
)
class PricingPage(rio.Component):
    """
    The Pricing page of the website.

    This page provides detailed pricing information for Services, including
    various pricing plans and frequently asked questions (FAQs) to assist users
    in making informed decisions.

    ## Attributes:

    `duration`: The duration of the pricing plan.
    """

    duration: str = "Monthly"

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for desktop devices.
        """
        return rio.Column(
            comps.PricingSection(),
            comps.FaqSection(),
            spacing=5,  # Consistent spaceing for desktop readability
            align_x=0.5,  # Center horizontally
            align_y=0,  # Align to the top vertically
            min_width=80,  # Fixed width to ensure proper layout on larger screens
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.
        """
        return rio.Column(
            comps.PricingSection(),
            comps.FaqSection(),
            spacing=5,  # Consistent spacing for mobile readability
            align_x=0.5,  # Center horizontally
            align_y=0,  # Align to the top vertically
            margin_x=1,  # Horizontal margin for compact layout on mobile
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
