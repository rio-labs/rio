# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme, utils

# </additional-imports>


# <component>
class CardSection(rio.Component):
    """
    A responsive section displaying a header and a list of `HeroCard`
    components.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Builds the column layout optimized for desktop devices.

        The desktop layout includes:
        - A title and description centered at the top.
        - Two rows of `HeroCard` components.
        - Proper spacing and alignment for desktop readability.
        """
        # Space between elements
        spacing = 2

        # First row of cards for the SERVICE_POWER
        row_1 = rio.Row(spacing=spacing)
        for icon, title, description in utils.SERVICE_POWER:
            # Add a HeroCard for each item
            row_1.add(
                comps.HeroCard(
                    icon,
                    title,
                    description,
                ),
            )

        # Second row of cards for the SERVICE_SPEED
        row_2 = rio.Row(spacing=spacing)
        for icon, title, description in utils.SERVICE_SPEED:
            # Add a HeroCard for each item
            row_2.add(
                comps.HeroCard(
                    icon,
                    title,
                    description,
                ),
            )

        # Combine rows into a single column with same spacing
        content = rio.Column(
            row_1,
            row_2,
            spacing=spacing,
        )

        # Combine title, description, and content into the full section
        return rio.Column(
            # Add Section Title
            rio.Text(
                "Why choose our service?",
                style=theme.BOLD_SECTION_TITLE_DESKTOP,
                justify="center",
            ),
            # Add Section Description
            rio.Text(
                "Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis.",
                font_size=1.1,
                justify="center",
            ),
            # Add the content of cards
            content,
            spacing=2,  # Space between title, description, and content
            align_x=0.5,  # Center-align the entire section
            min_width=80,  # Fixed width for desktop
        )

    def _mobile_build(self) -> rio.Component:
        """
        Builds the column layout optimized for mobile devices.

        The mobile layout includes:
        - A title and description at the top.
        - A single column of `HeroCard` components.
        - Adjusted font sizes and spacing for mobile readability.
        """
        # Space between elements
        spacing = 2

        # Combine all cards into a single column for mobile
        content = rio.Column(spacing=spacing)
        # Add a HeroCard for each item
        for icon, title, description in utils.SERVICE_POWER:
            content.add(
                comps.HeroCard(
                    icon,
                    title,
                    description,
                ),
            )
        for icon, title, description in utils.SERVICE_SPEED:
            content.add(
                comps.HeroCard(
                    icon,
                    title,
                    description,
                ),
            )

        return rio.Column(
            # Add section title
            rio.Text(
                "Why choose our service?",
                style=theme.BOLD_SECTION_TITLE_MOBILE,
            ),
            # Add section description
            rio.Text(
                "Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis.",
                overflow="wrap",
            ),
            # Add the column of cards
            content,
            spacing=2,  # Space between title, description, and content
            align_x=0.5,  # Center-align the entire section
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
