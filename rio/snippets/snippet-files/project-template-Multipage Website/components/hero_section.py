from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class HeroSection(rio.Component):
    """
    A responsive hero section that displays a call to action for building SaaS applications.

    The section includes:
    - A button linking to the Rio website.
    - A main title and subtitle.
    - A row of call-to-action buttons.
    - An image placeholder showcasing the hero visual.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Builds the column layout optimized for desktop devices.
        """
        return rio.Column(
            # Add button linking to the Rio website
            comps.OutlinedColoredButton(
                text="Made with Rio",
                target_url="https://rio.dev",
                icon="material/open_in_new",
                align_x=0.5,
            ),
            # Add main title
            rio.Text(
                "Build your SaaS in seconds",
                justify="center",
                style=theme.BOLD_SECTION_TITLE_DESKTOP,
            ),
            # Add subtitle
            rio.Text(
                "This template demonstrates most of Rio's components. It's a great starting point to build your own SaaS.",
                justify="center",
                font_size=theme.ACTION_TEXT_HEIGHT,
            ),
            # Add call-to-action buttons
            rio.Row(
                rio.Button(
                    rio.Row(
                        rio.Text("Get started"),
                        rio.Icon("material/arrow_forward"),
                        align_x=0.5,
                        spacing=1,
                        margin_x=1,
                    ),
                    color=rio.Color.from_hex("ffffff"),
                ),
                comps.OutlinedNeutralButton(
                    text="Use this template", icon="thirdparty/github_logo"
                ),
                #
                spacing=1,
                align_x=0.5,
            ),
            # Add image placeholder
            comps.ImagePlaceholder(
                image_min_height=40,
                margin_top=5,
            ),
            margin_top=5,  # Top margin for the hero section
            spacing=2,  # Space between elements
            align_x=0.5,  # Center-align the column
            min_width=80,  # Fixed width for desktop layout
        )

    def _mobile_build(self) -> rio.Component:
        """
        Builds the column layout optimized for mobile devices.
        """
        return rio.Column(
            # Add button linking to the Rio website
            comps.OutlinedColoredButton(
                text="Made with Rio",
                target_url="https://rio.dev",
                icon="material/open_in_new",
                align_x=0.5,
            ),
            rio.Column(
                # Split main title so it fits on mobile screens with preferred
                # text wrapping
                rio.Text(
                    "Build your SaaS",
                    justify="center",
                    style=theme.BOLD_SMALLER_SECTION_TITLE_MOBILE,
                ),
                rio.Text(
                    "in seconds",
                    justify="center",
                    style=theme.BOLD_SMALLER_SECTION_TITLE_MOBILE,
                ),
            ),
            # Add subtitle
            rio.Text(
                "This template demonstrates most of Rio's components. It's a great starting point to build your own SaaS.",
                justify="center",
                overflow="wrap",
                font_size=theme.ACTION_TEXT_HEIGHT,
            ),
            # Add call-to-action buttons
            rio.Column(
                rio.Button(
                    rio.Row(
                        rio.Text("Get started"),
                        rio.Icon("material/arrow_forward"),
                        align_x=0.5,
                        spacing=1,
                    ),
                    color=rio.Color.from_hex("ffffff"),
                ),
                comps.OutlinedNeutralButton(
                    text="Use this template", icon="thirdparty/github_logo"
                ),
                align_x=0.5,
                spacing=1,
            ),
            # Add image placeholder
            comps.ImagePlaceholder(
                image_min_height=13,
                margin_top=3,
            ),
            spacing=2,
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
