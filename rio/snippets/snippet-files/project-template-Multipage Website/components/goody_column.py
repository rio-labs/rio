# <additional-imports>
import rio

from .. import theme

# </additional-imports>


# <component>
class GoodyColumn(rio.Component):
    """
    A column that displays the amount of goodies that come with a plan.


    ## Attributes:

    `amount_goodies`: The amount of goodies that come with the plan.

    `goodie_text`: The text that describes the goodies. For example, "GB Storage".
    """

    amount_goodies: int
    goodie_text: str

    def build(self) -> rio.Component:
        # Determine if the text should be pluralized based on the quantity of
        # goodies
        if self.amount_goodies > 1 and not self.goodie_text == "GB Storage":
            plural = "s"
        else:
            plural = ""

        # Build and return the row component with the icon and text
        return rio.Row(
            rio.Icon(
                "material/check_circle:fill",
                fill=self.session.theme.primary_color,
            ),
            rio.Text(
                f"{self.amount_goodies} {self.goodie_text}{plural}",
                style=theme.DARK_TEXT_SMALLER,
            ),
            align_x=0,  # Align the row's contents horizontally to the left
            spacing=0.8,  # Add spacing between the icon and text
        )


# </component>
