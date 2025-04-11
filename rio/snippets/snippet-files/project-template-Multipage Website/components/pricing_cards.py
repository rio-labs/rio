import typing as t

# <additional-imports>
import rio

from .. import components as comps
from .. import theme

# </additional-imports>


# <component>
GOODIES = [
    "GB Storage",
    "Email Account",
    "Domain",
    "Website",
    "Database",
    "SSL Certificate",
    "Support Ticket",
]


class PricingCards(rio.Component):
    """
    A component that displays pricing information for different subscription
    plans.


    ## Attributes:

    `plan_type`: The type of the plan.

    `plan_description`: A description of the plan's features.

    `duration`: The billing cycle of the plan (e.g., "Monthly" or "Yearly").

    `monthly_price`: The price for a monthly subscription.

    `yearly_price`: The price for a yearly subscription.

    `amount_goodies`: The number of included goodies in the plan.

    `is_selected`: Whether the plan is currently selected by the user.
    """

    plan_type: t.Literal["Basic", "Standard", "Premium"]
    plan_description: str
    duration: str
    monthly_price: float
    yearly_price: float
    amount_goodies: int

    is_selected: bool = False

    def build(self) -> rio.Component:
        # Determine pricing details based on the subscription duration
        if self.duration == "Monthly":
            duration = "month"
            price = self.monthly_price
        else:
            duration = "year"
            price = self.yearly_price

        # Define the button based on the selection status
        if self.is_selected:
            button = rio.Button(
                rio.Text(
                    "Get Started",
                    fill=self.session.theme.background_color,
                    align_x=0.5,
                ),
                color=rio.Color.from_hex("ffffff"),
                margin_y=1,
            )
        else:
            button = comps.OutlinedNeutralButton("Get Started", margin_y=1)

        # Create a column of goodies based on the amount of goodies included in
        # the plan
        goody_column = rio.Column(spacing=1)
        # Loop through the list of goodies and add them to the column
        for goodie in GOODIES:
            goody_column.add(
                comps.GoodyColumn(
                    amount_goodies=self.amount_goodies,
                    goodie_text=goodie,
                )
            )

        # Construct the card content
        content = rio.Column(
            rio.Text(
                self.plan_type,
                font_weight="bold",
                font_size=1.8,
                fill=theme.TEXT_FILL_BRIGHTER,
            ),
            rio.Text(
                self.plan_description,
                style=theme.DARKER_TEXT,
            ),
            rio.Row(
                rio.Text(
                    f"${price}",
                    font_weight="bold",
                    font_size=1.8,
                    fill=theme.TEXT_FILL_BRIGHTER,
                ),
                rio.Text(
                    f" /{duration}",
                    style=theme.DARKER_TEXT,
                    align_y=0.85,
                ),
                align_x=0,  # Align the price and duration horizontally
                margin_top=1,  # Add margin above the price section
            ),
            # Add the button to the card
            button,
            # Add the column of goodies to the card
            goody_column,
            spacing=1,  # Add spacing between card elements
            margin=3,  # Add outer margin for the card content
        )

        # Wrap the content in a rectangle with styling based on the selection
        return rio.Rectangle(
            content=content,
            fill=rio.Color.TRANSPARENT,
            corner_radius=self.session.theme.corner_radius_medium,
            # Highlight the border if selected
            stroke_color=(
                self.session.theme.primary_color
                if self.is_selected
                else theme.NEUTRAL_COLOR_BRIGHTER
            ),
            # Adjust border thickness if selected
            stroke_width=0.15 if self.is_selected else 0.1,
        )


# </component>
