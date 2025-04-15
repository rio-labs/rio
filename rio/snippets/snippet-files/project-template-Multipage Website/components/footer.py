from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models

# </additional-imports>


# <component>
class Footer(rio.Component):
    """
    A responsive footer component that displays company-related information and
    navigation links.

    The footer is organized into sections for resources, features, company
    information, and a newsletter subscription option. The layout adapts to
    desktop and mobile devices.
    """

    def build(self) -> rio.Component:
        """
        Constructs the footer layout based on the device type.

        For desktop:
        - Displays sections in a row layout with a minimum width.

        For mobile:
        - Adjusts the layout to a column with additional margins and spacing.
        """
        # Get the device type from the session
        device = self.session[data_models.PageLayout].device

        # Define the main content layout based on the device type
        if device == "desktop":
            content = rio.Row(
                margin_top=2,
                align_x=0.5,
                min_width=80,
            )
        else:
            content = rio.Row(
                spacing=2,
            )

        # Add the Resources section
        content.add(
            rio.Column(
                rio.Text(
                    "Resources",
                    font_weight="bold",
                    font_size=0.9,
                    margin_bottom=0.5,
                ),
                comps.FakeLink("Help center"),
                comps.FakeLink("Docs"),
                comps.FakeLink("Roadmap"),
                comps.FakeLink("Changelog"),
                spacing=1,
            ),
        )

        # Add the Features section
        content.add(
            rio.Column(
                rio.Text(
                    "Features",
                    font_weight="bold",
                    font_size=0.9,
                    margin_bottom=1,
                ),
                comps.FakeLink("Affiliates"),
                comps.FakeLink("Portal"),
                comps.FakeLink("Jobs"),
                comps.FakeLink("Sponsors"),
                spacing=1,
            ),
        )

        # Add the Company section
        content.add(
            rio.Column(
                rio.Text(
                    "Company",
                    font_weight="bold",
                    font_size=0.9,
                    margin_bottom=1,
                ),
                comps.FakeLink("About"),
                comps.FakeLink("Pricing"),
                comps.FakeLink("Careers"),
                comps.FakeLink("Blog"),
                spacing=1,
            ),
        )

        # Add the newsletter subscription section
        if device == "desktop":
            content.add(
                rio.Column(
                    rio.Text(
                        "Subscribe to our newsletter",
                        font_weight="bold",
                    ),
                    comps.SubscribeInputButton(),
                    spacing=1,
                    align_y=0,
                ),
            )
        else:
            # Adjust the layout for mobile with the subscription section
            content = rio.Column(
                content,  # Existing content
                rio.Column(
                    rio.Text(
                        "Subscribe to our newsletter",
                        font_weight="bold",
                    ),
                    comps.SubscribeInputButton(),
                    spacing=1,
                    align_y=0,
                ),
                margin_top=2,
                margin_x=1,
                spacing=2,
            )

        # Return the complete footer structure
        return rio.Column(
            # Divider line above the footer
            rio.Rectangle(
                fill=self.session.theme.neutral_color,
                min_height=0.1,  # Thin line for visual separation
            ),
            content,  # Main footer content
            margin_y=5,  # Add vertical margin around the footer
        )


# </component>
