# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class FaqSection(rio.Component):
    """
    A responsive FAQ section displaying frequently asked questions.

    This section consists of:
    - A title and subtitle providing an introduction to the FAQ.
    - Multiple `FAQ` components for individual questions and answers.
    - Separators for visual organization.
    - Layout adjustments for desktop and mobile devices.
    """

    def _desktop_build(self) -> rio.Component:
        """
        Builds the column layout optimized for desktop devices.
        """
        return rio.Column(
            # Add Section Title
            rio.Text(
                "Frequently asked questions",
                justify="center",
                style=theme.BOLD_BIGGER_SECTION_TITLE_DESKTOP,
            ),
            # Add Section Subtitle
            rio.Text(
                "At vero eos et accusam et justo duo dolores et ea rebum.",
                justify="center",
                style=theme.DARK_TEXT_BIGGER,
            ),
            # Add FAQ items
            rio.Column(
                comps.Faq(
                    header="What is the refund policy?",
                    body="Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="How can I cancel my subscription?",
                    body="Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="How does a free trial work?",
                    body="Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="Can I switch plans later?",
                    body="Stet clita kasd gubergren, no sea takimata sanctus, sed diam voluptua.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="Do you offer refunds?",
                    body="Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="Do you offer support?",
                    body="Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla.",
                    is_last=True,  # Indicates this is the last FAQ and adds an extra Separator when open
                ),
                margin_top=4,  # Top margin for the FAQ list
                align_x=0.5,  # Center-align the column
                min_width=60,  # Fixed width for the FAQ section
            ),
            margin_bottom=10,  # Bottom margin for the section
            margin_top=5,  # Top margin for the section
            align_x=0.5,  # Center-align the section
            min_width=80,  # Fixed width for the section
            spacing=1,  # Space between elements
            align_y=0,  # Align vertically at the top
        )

    def _mobile_build(self) -> rio.Component:
        """
        Builds the column layout optimized for mobile devices.
        """
        return rio.Column(
            # Add Section Title
            rio.Text(
                "Frequently asked questions",
                justify="center",
                overflow="wrap",
                style=theme.BOLD_SECTION_TITLE_MOBILE,
            ),
            # Add Section Subtitle
            rio.Text(
                "At vero eos et accusam et justo duo dolores et ea rebum.",
                justify="center",
                overflow="wrap",
                style=theme.DARKER_TEXT,
            ),
            # Add FAQ items
            rio.Column(
                comps.Faq(
                    header="What is the refund policy?",
                    body="Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="How can I cancel my subscription?",
                    body="Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="How does a free trial work?",
                    body="Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="Can I switch plans later?",
                    body="Stet clita kasd gubergren, no sea takimata sanctus, sed diam voluptua.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="Do you offer refunds?",
                    body="Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam.",
                ),
                rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                comps.Faq(
                    header="Do you offer support?",
                    body="Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla.",
                    is_last=True,  # Indicates this is the last FAQ and adds an extra Separator when open
                ),
                margin_top=4,  # Top margin for the FAQ list
            ),
            spacing=1,  # Space between elements
            align_y=0,  # Align vertically at the top
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
