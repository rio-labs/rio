# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme, utils

# </additional-imports>


# <component>
class Testimonials(rio.Component):
    """
    Testimonials Component.

    This component displays a section of customer testimonials, organized in a
    responsive layout optimized for both desktop and mobile devices. It includes
    a header, sub-header, a brief description, and a collection of individual
    testimonials.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for desktop devices.
        """
        spacing = 2  # Space between columns and rows

        # Initialize four columns to distribute testimonials evenly
        content = rio.Row(spacing=spacing, margin_top=4)
        column_1 = rio.Column(spacing=spacing)
        column_2 = rio.Column(spacing=spacing)
        column_3 = rio.Column(spacing=spacing)
        column_4 = rio.Column(spacing=spacing)

        # Add the first testimonial to column 1
        column_1.add(
            comps.Testimonial(
                img=utils.TESTIMONIALS[0].image,
                quote=utils.TESTIMONIALS[0].quote,
                name=utils.TESTIMONIALS[0].name,
                company=utils.TESTIMONIALS[0].company,
            )
        )
        # Add a spacer for consistent spacing
        column_1.add(
            rio.Spacer(),
        )

        # Add the next two testimonials to column 2
        for i in range(1, 3):
            column_2.add(
                comps.Testimonial(
                    img=utils.TESTIMONIALS[i].image,
                    quote=utils.TESTIMONIALS[i].quote,
                    name=utils.TESTIMONIALS[i].name,
                    company=utils.TESTIMONIALS[i].company,
                )
            )
        # Add a spacer for consistent spacing
        column_2.add(
            rio.Spacer(),
        )

        # Add the next two testimonials to column 3
        for i in range(3, 5):
            column_3.add(
                comps.Testimonial(
                    img=utils.TESTIMONIALS[i].image,
                    quote=utils.TESTIMONIALS[i].quote,
                    name=utils.TESTIMONIALS[i].name,
                    company=utils.TESTIMONIALS[i].company,
                )
            )
        # Add a spacer for consistent spacing
        column_3.add(
            rio.Spacer(),
        )

        # Add the last testimonial to column 4
        column_4.add(
            comps.Testimonial(
                img=utils.TESTIMONIALS[-1].image,
                quote=utils.TESTIMONIALS[-1].quote,
                name=utils.TESTIMONIALS[-1].name,
                company=utils.TESTIMONIALS[-1].company,
            )
        )
        # Add a spacer for consistent spacing
        column_4.add(
            rio.Spacer(),
        )

        # Combine all columns into a single row
        content = rio.Row(
            column_1,
            column_2,
            column_3,
            column_4,
            spacing=spacing,
        )

        # Construct the main testimonials section with headers and content
        return rio.Column(
            rio.Text(
                "Testimonials",
                fill=self.session.theme.primary_color,
                font_weight="bold",
                justify="center",
            ),
            # Section Title
            rio.Text(
                "What our customers are saying.",
                style=theme.BOLD_SECTION_TITLE_DESKTOP,
                justify="center",
            ),
            # Brief description
            rio.Text(
                "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam.",
                overflow="wrap",
                justify="center",
                font_size=1.1,
                margin_bottom=4,
            ),
            # Testimonials Content
            content,
            spacing=1,  # Space between elements in the column
            align_x=0.5,  # Center the column horizontally
            align_y=0,  # Align the column to the top vertically
            min_width=80,  # Fixed width to ensure proper layout on larger screens
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.
        """
        spacing = 2  # Space between testimonials
        # Initialize a single column to stack testimonials vertically
        content = rio.Column(
            spacing=spacing,
            margin_top=2,
        )

        # Add all testimonials to the single column
        for i in range(0, len(utils.TESTIMONIALS)):
            content.add(
                comps.Testimonial(
                    img=utils.TESTIMONIALS[i].image,
                    quote=utils.TESTIMONIALS[i].quote,
                    name=utils.TESTIMONIALS[i].name,
                    company=utils.TESTIMONIALS[i].company,
                )
            )

        # Construct the main testimonials section with headers and content
        return rio.Column(
            rio.Text(
                "Testimonials",
                fill=self.session.theme.primary_color,
                font_weight="bold",
                justify="center",
            ),
            # Section Title
            rio.Text(
                "What our customers are saying.",
                overflow="wrap",
                style=theme.BOLD_SECTION_TITLE_MOBILE,
                justify="center",
            ),
            # Brief Description
            rio.Text(
                "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam.",
                overflow="wrap",
                justify="center",
                font_size=1,
            ),
            # Testimonials Content
            content,
            spacing=1,  # Space between elements in the column
            align_y=0,  # Align the column to the top vertically
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
