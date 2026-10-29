import typing as t

import rio

# <additional-imports>
from .. import components as comps

# </additional-imports>


# <component>
class InboxHeader(rio.Component):
    """
    A header component for the inbox page that displays the inbox title and a
    switcher bar.


    ## Attributes:

    `switcher_option`: The selected value of the switcher bar
    """

    switcher_option: t.Literal["All", "Unread"]

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Separator(color=self.session.theme.neutral_color),
            rio.Row(
                rio.Text(
                    "Inbox",
                    font_weight="bold",
                    align_x=0,
                    align_y=0.5,
                ),
                comps.ColoredRectangle(
                    color=self.session.theme.primary_color, content=25
                ),
                # Push the switcher bar to the right
                rio.Spacer(),
                rio.SwitcherBar(
                    values=["All", "Unread"],
                    selected_value=self.bind().switcher_option,
                    color=rio.Color.from_hex("ffffff"),
                ),
                spacing=0.5,
                align_x=0,
                align_y=0,
                min_height=4,
                min_width=23,
                margin_x=1,
            ),
            rio.Separator(color=self.session.theme.neutral_color),
            align_x=0,
            align_y=0,
        )


# </component>
