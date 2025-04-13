# <additional-imports>
import rio

from .. import data_models, theme

# </additional-imports>


# <component>
class GetStarted(rio.Component):
    """
    A responsive component that displays a call-to-action section with a "Get
    started" message and a button.

    The component adapts its layout and text styles for desktop and mobile
    devices.
    """

    def build(self) -> rio.Component:
        """
        Constructs the "Get Started" section.

        For desktop:
        - Larger text sizes and a fixed width layout.
        - Includes a button to "Buy now."

        For mobile:
        - Adjusted text sizes and wrapping text for smaller screens.
        - Compact layout with responsive widths.
        """
        # Get the device type from the session
        device = self.session[data_models.PageLayout].device
        # Set styles and layout behavior based on the device type
        if device == "desktop":
            header_text_style: rio.TextStyle = (
                theme.BOLD_SMALLER_SECTION_TITLE_DESKTOP
            )
            sub_header_text_size = 1.1
            overflow = "nowrap"

        else:
            header_text_style: rio.TextStyle = theme.BOLD_SECTION_TITLE_MOBILE
            sub_header_text_size = 1
            overflow = "wrap"

        # Construct the content column
        content = rio.Column(
            rio.Text(
                "Get started today",
                justify="center",
                style=header_text_style,
            ),
            rio.Text(
                "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy.",
                justify="center",
                overflow=overflow,  # Text wrapping based on device
                font_size=sub_header_text_size,
            ),
            rio.Button(
                "Buy now",
                color=rio.Color.from_hex("ffffff"),
                margin=0.5,
                align_x=0.5,
                align_y=0.5,
            ),
            align_x=0.5,
            align_y=0.5,
            spacing=3,
            margin=2,
        )

        # Return a rectangle with styling based on the device type
        if device == "desktop":
            # Desktop-specific layout
            return rio.Rectangle(
                content=content,
                fill=self.session.theme.neutral_color,
                stroke_width=0.1,
                stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
                corner_radius=self.session.theme.corner_radius_medium,
                align_x=0.5,  # Center-align rectangle horizontally
                min_height=30,  # Fixed height for desktop
                min_width=80,  # Fixed width for desktop layout
            )
        else:
            # Mobile-specific layout
            return rio.Rectangle(
                content=content,
                fill=self.session.theme.neutral_color,
                stroke_width=0.1,
                stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
                corner_radius=self.session.theme.corner_radius_medium,
                min_height=20,  # Smaller minimum height for mobile
                min_width=0,  # Responsive width for mobile
            )


# </component>
