# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, theme

# </additional-imports>


# <component>
class PricingSection(rio.Component):
    """
    PricingSection Component.

    This component displays the pricing plans available to users, highlighting
    different tiers such as Basic, Standard, and Premium. It includes headers,
    descriptions, and a switcher to toggle between "Monthly" and "Yearly"
    billing durations. The layout is responsive, ensuring optimal display on
    both desktop and mobile devices.


    ## Attributes:

    `duration`: The selected billing duration, either "Monthly" or "Yearly".
    """

    duration: str = "Monthly"

    def _desktop_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.

        Build a vertical column containing headers, descriptions, a duration
        switcher, and a row of pricing cards. This layout leverages the larger
        screen space of desktop devices to display pricing options side by side
        for better comparison.
        """
        return rio.Column(
            # Main header for the pricing section
            rio.Text(
                "A plan for every need",
                justify="center",
                style=theme.BOLD_BIGGER_SECTION_TITLE_DESKTOP,
            ),
            # Sub-header providing additional context
            rio.Text(
                "Our plans are designed to meet the requirements of both beginners and players. Get the right plan that suits you.",
                justify="center",
                style=theme.DARK_TEXT_BIGGER,
            ),
            # Switcher to toggle between "Monthly" and "Yearly" durations
            comps.CustomSwitcherBar(
                # Bind the switcher's selected value to the 'duration' attribute
                # This allows the switcher to update the duration when toggled
                duartion=self.bind().duration,
                margin_top=2,
            ),
            # Row containing multiple pricing cards
            rio.Row(
                # Basic plan pricing card
                comps.PricingCards(
                    plan_type="Basic",
                    plan_description="A basic plan for individuals.",
                    duration=self.duration,
                    monthly_price=9.9,
                    yearly_price=99.9,
                    amount_goodies=1,  # Number of additional benefits included
                ),
                comps.PricingCards(
                    plan_type="Standard",
                    plan_description="A standard plan for small teams.",
                    duration=self.duration,
                    monthly_price=19.9,
                    yearly_price=199.9,
                    is_selected=True,  # Indicates that this plan is currently highlighted or recommended
                    amount_goodies=10,  # Number of additional benefits included
                ),
                comps.PricingCards(
                    plan_type="Premium",
                    plan_description="A premium plan for large teams.",
                    duration=self.duration,
                    monthly_price=29.9,
                    yearly_price=299.9,
                    amount_goodies=100,  # Number of additional benefits included
                ),
                spacing=2,  # Space between each pricing card
                margin_top=3,  # Top margin for spacing above the row of pricing cards
            ),
            spacing=1,  # Space between elements within the column
            align_x=0.5,  # Center-align the column horizontally within its parent
            align_y=0,  # Align the column to the top vertically
            min_width=80,  # Fixed width to ensure proper layout on larger screens
        )

    def _mobile_build(self) -> rio.Component:
        """
        Build the layout optimized for mobile devices.

        Build a vertical column containing headers, descriptions, a duration
        switcher, and a stacked column of pricing cards. This single-column
        layout ensures that content is easily readable on smaller screens.
        """
        return rio.Column(
            # Main header for the pricing section
            rio.Text(
                "A plan for every need",
                justify="center",  # Center-align the text horizontally
                overflow="wrap",  # Allow text to wrap to the next line if necessary
                style=theme.BOLD_BIGGER_SECTION_TITLE_MOBILE,
            ),
            # Sub-header providing additional context
            rio.Text(
                "Our plans are designed to meet the requirements of both beginners and players. Get the right plan that suits you.",
                justify="center",  # Center-align the text horizontally
                overflow="wrap",  # Allow text to wrap to the next line if necessary
                style=theme.DARKER_TEXT,
            ),
            # Switcher to toggle between "Monthly" and "Yearly" durations
            comps.CustomSwitcherBar(
                # Bind the switcher's selected value to the 'duration' attribute
                # This allows the switcher to update the duration when toggled
                duartion=self.bind().duration,
                margin_top=2,
            ),
            # Column containing multiple pricing cards stacked vertically
            rio.Column(
                comps.PricingCards(
                    plan_type="Basic",
                    plan_description="A basic plan for individuals.",
                    duration=self.duration,
                    monthly_price=9.9,
                    yearly_price=99.9,
                    amount_goodies=1,  # Number of additional benefits included
                ),
                comps.PricingCards(
                    plan_type="Standard",
                    plan_description="A standard plan for small teams.",
                    duration=self.duration,
                    monthly_price=19.9,
                    yearly_price=199.9,
                    is_selected=True,  # Indicates that this plan is currently highlighted or recommended
                    amount_goodies=10,  # Number of additional benefits included
                ),
                comps.PricingCards(
                    plan_type="Premium",
                    plan_description="A premium plan for large teams.",
                    duration=self.duration,
                    monthly_price=29.9,
                    yearly_price=299.9,
                    amount_goodies=100,  # Number of additional benefits included
                ),
                spacing=2,  # Space between each pricing card
                margin_top=3,  # Top margin for spacing above the column of pricing cards
            ),
            spacing=1,  # Space between elements within the column
            align_x=0.5,  # Center-align the column horizontally within its parent
            align_y=0,  # Align the column to the top vertically
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
