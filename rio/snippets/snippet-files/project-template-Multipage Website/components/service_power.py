# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme, utils

# </additional-imports>


# <component>
class ServicePower(rio.Component):
    """
    ServicePower Component.

    This component showcases the strengths and capabilities of our service. It
    includes a header, sub-header, and a list of bullet points highlighting key
    features. The layout is responsive, providing an optimized view for both
    desktop and mobile devices.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for desktop devices.

        Builds a horizontal row containing a major column with service details
        and an image placeholder. This layout leverages the ample screen space
        of desktop devices to display content side by side for enhanced
        readability and visual appeal.
        """
        return rio.Row(
            # Major column containing the header, sub-header, and bullet points
            comps.MajorColumn(
                header="The power of our service",
                sub_header="Aliqua labore laboris fugiat. Reprehenderit exercitation eu commodo. Officia nostrud sit et aliqua ea ex sunt minim incididunt sunt.",
                # List of bullet points detailing service power
                content=utils.SERVICE_POWER,
            ),
            # Placeholder for an image related to the service
            comps.ImagePlaceholder(
                image_min_height=20,  # Fixed height for the image on desktop
                min_width=39,  # Fixed width for the image on desktop
            ),
            spacing=2,  # Space between the major column and the image placeholder
            align_x=0.5,  # Center align the row horizontally
            align_y=0,  # Align the row to the top vertically
            min_width=80,  # Fixed width to ensure proper layout on larger screens
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.

        Builds a vertical column containing the major service details and an
        image placeholder. This single-column layout ensures that content is
        easily readable on mobile devices.
        """
        return rio.Column(
            # Major column containing the header, sub-header, and bullet points
            comps.MajorColumn(
                header="The power of our service",
                sub_header="Aliqua labore laboris fugiat. Reprehenderit exercitation eu commodo. Officia nostrud sit et aliqua ea ex sunt minim incididunt sunt.",
                # List of bullet points detailing service power
                content=utils.SERVICE_POWER,
            ),
            # Placeholder for an image related to the service
            comps.ImagePlaceholder(
                # Minimum height for the image on mobile
                image_min_height=theme.MOBILE_IMAGE_HEIGHT,
                # Full width on mobile subtracting margin_x
                min_width=self.session.window_width - 2,
            ),
            spacing=2,  # Space between the major column and the image placeholder
            align_x=0,  # Align the column to the start horizontally
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
