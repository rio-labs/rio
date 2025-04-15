# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class MajorColumn(rio.Component):
    """
    A responsive column component that adapts to desktop and mobile layouts.

    The column includes a header, a sub-header, and a list of bullet points.


    ## Attributes:

    `header`: The main title of the column.

    `sub_header`: The subtitle or additional description of the column.

    `content`: A list of tuples where each tuple represents a bullet point with:
        - `icon`: The icon for the bullet point.
        - `title`: The title of the bullet point.
        - `description`: A brief description for the bullet point.
    """

    header: str
    sub_header: str
    content: list[tuple[str, str, str]]

    def _desktop_build(self) -> rio.Component:
        """
        Builds the column layout optimized for desktop devices.
        """
        # Create a column to hold the bullet points
        content = rio.Column(spacing=1)

        # Add each bullet point to the column
        for icon, title, description in self.content:
            content.add(
                comps.BulletPoint(
                    icon=icon,
                    title=title,
                    description=description,
                ),
            )

        return rio.Column(
            # Add header
            rio.Text(
                self.header,
                style=theme.BOLD_SECTION_TITLE_DESKTOP,
            ),
            # Add sub-header
            rio.Text(
                self.sub_header,
                overflow="wrap",  # Ensure text wraps if needed
                font_size=1.1,
            ),
            # Add the column of bullet points
            content,
            spacing=2,  # Space between elements in the column
            align_x=0,  # Align content to the left
            align_y=0,  # Align column vertically to the top
            min_width=39,  # Fixed width for desktop layout
        )

    def _mobile_build(self) -> rio.Component:
        """
        Builds the column layout optimized for mobile devices.
        """
        # Create a column to hold the bullet points
        content = rio.Column(spacing=1)

        # Add each bullet point to the column
        for icon, title, description in self.content:
            content.add(
                comps.BulletPoint(
                    icon=icon,
                    title=title,
                    description=description,
                ),
            )

        return rio.Column(
            # Add header
            rio.Text(
                self.header,
                style=theme.BOLD_SECTION_TITLE_MOBILE,
            ),
            # Add sub-header
            rio.Text(
                self.sub_header,
                overflow="wrap",  # Ensure text wraps if needed
            ),
            # Add the column of bullet points
            content,
            spacing=2,  # Space between elements in the column
            align_x=0,  # Align content to the left
            align_y=0,  # Align column vertically to the top
        )

    def build(self) -> rio.Component:
        """
        Build and return the page layout based on the user's device type.

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
