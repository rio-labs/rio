# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme, utils

# </additional-imports>


# <component>
class ServiceSpeed(rio.Component):
    """
    ServiceSpeed Component.

    This component highlights the speed and efficiency of our service. It
    includes a header, sub-header, and a list of bullet points detailing key
    aspects that demonstrate the rapid and reliable nature of our offerings. The
    layout is responsive, ensuring an optimized view for both desktop and mobile
    devices.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for desktop devices.

        Builds a horizontal row containing an image placeholder and a major
        column with service details. This side-by-side arrangement leverages the
        spacious desktop screen to present content clearly and attractively.
        """
        return rio.Row(
            # Placeholder for an image related to the service speed
            comps.ImagePlaceholder(
                image_min_height=20,  # Fixed height for the image on desktop
                min_width=39,  # Fixed width for the image on desktop
            ),
            # Major column containing the header, sub-header, and bullet points
            comps.MajorColumn(
                header="The speed of our service",
                sub_header="Aliqua labore laboris fugiat. Reprehenderit exercitation eu commodo. Officia nostrud sit et aliqua ea ex sunt minim incididunt sunt.",
                # List of bullet points detailing service speed
                content=utils.SERVICE_SPEED,
            ),
            spacing=2,  # Space between the image placeholder and the major column
            align_x=0.5,  # Center align the row horizontally
            align_y=0,  # Align the row to the top vertically
            min_width=80,  # Fixed width to ensure proper layout on larger screens
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.

        Builds a vertical column containing the major service details and an image
        placeholder. This stacked arrangement ensures that content is easily readable
        and navigable on smaller screens typical of mobile devices.
        """
        return rio.Column(
            # Major column containing the header, sub-header, and bullet points
            comps.MajorColumn(
                header="The speed of our service",
                sub_header="Aliqua labore laboris fugiat. Reprehenderit exercitation eu commodo. Officia nostrud sit et aliqua ea ex sunt minim incididunt sunt.",
                # List of bullet points detailing service speed
                content=utils.SERVICE_SPEED,
            ),
            # Placeholder for an image related to the service speed
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
