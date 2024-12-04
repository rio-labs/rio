# <additional-imports>
import rio

from .. import theme

# </additional-imports>


# <component>
class CustomSwitcherBar(rio.Component):
    """
    MySwitcher Component.

    This component provides a toggle switch allowing users to select between
    "Monthly" and "Yearly" durations. It is styled to blend seamlessly with the
    website's theme, featuring rounded corners and a transparent background with
    a subtle border.

    ## Attributes:

    `duartion`: The selected duration, either "Monthly" or "Yearly".
    """

    duartion: str = "Monthly"

    def build(self) -> rio.Component:
        return rio.Rectangle(
            # The switcher bar allowing users to select between "Monthly" and
            # "Yearly"
            content=rio.SwitcherBar(
                values=["Monthly", "Yearly"],
                # The selected value is bound to the "duration" attribute,
                # therefore, no eventhandler is needed
                selected_value=self.bind().duartion,
                color=rio.Color.from_hex("#ffffff"),
                align_x=0.5,  # Horizontally center the switcher within the rectangle
                min_width=10,  # Fixed width of the switcher bar
                margin=0.3,  # Margin around the switcher bar for spacing
            ),
            fill=rio.Color.TRANSPARENT,
            # Add a subtle border to the rectangle for visual separation
            stroke_width=0.1,
            stroke_color=theme.NEUTRAL_COLOR_BRIGHTER,
            # Fully rounded corners to create a pill-shaped rectangle.
            corner_radius=99999,
            align_x=0.5,  # Horizontally center the rectangle within its parent
        )


# </component>
