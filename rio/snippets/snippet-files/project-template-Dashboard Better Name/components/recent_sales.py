from __future__ import annotations

import rio

# <additional-imports>
from .. import constants, data_models, theme

# </additional-imports>


# <component>
class SalesInfo(rio.Component):
    """
    A component that represents information about a customer's sale.

    This component displays details of a customer's sale, such as the customer's
    name, sale amount, date, and other relevant information. It uses Rio
    components to structure and style the content.


    ## Attributes:

    `customer_sale`: Containing details about the customer's sale.
    """

    customer_sale: data_models.CustomerSale

    def build(self) -> rio.Component:
        # Create the content to display the customer's sale information
        content = rio.Row(
            # Display the customer's image
            rio.Rectangle(
                fill=rio.ImageFill(
                    self.session.assets / self.customer_sale.image
                ),
                min_height=2.5,
                min_width=2.5,
                corner_radius=9999,
                align_y=0.5,
            ),
            rio.Column(
                rio.Text(
                    self.customer_sale.name,
                    style=theme.TEXT_STYLE_SMALL_BOLD,
                ),
                rio.Text(
                    self.customer_sale.email,
                    style=theme.TEXT_STYLE_DARKER_SMALL,
                ),
                spacing=0.4,
            ),
            # Add spacer to align the price to the right
            rio.Spacer(),
            rio.Text(
                f"${self.customer_sale.price}",
                font_weight="bold",
            ),
            margin=0.5,
            spacing=0.5,
        )

        # Style the content with a rectangle
        return rio.Rectangle(
            content=content,
            fill=self.session.theme.background_color,
            hover_fill=self.session.theme.neutral_color,
            corner_radius=self.session.theme.corner_radius_small,
            transition_time=0.2,
        )


class RecentSales(rio.Component):
    """
    A component that displays a list of recent sales.

    This component iterates through a collection of customer sales data and
    displays each sale using the `SalesInfo` component. It structures the sales
    information in a column layout and includes an icon for visual
    representation.
    """

    def build(self) -> rio.Component:
        # Add the recent sales
        sales_info = rio.Column(spacing=1)
        for customer_sales in constants.CUSTOMER_SALES.sales:
            sales_info.add(
                SalesInfo(customer_sales),
            )

        # Create the content to display the recent sales information
        content = rio.Column(
            rio.Row(
                rio.Icon(
                    "material/signal_cellular_alt",
                    min_height=3.5,
                    min_width=3.5,
                ),
                rio.Column(
                    rio.Text(
                        "Recent Sales",
                        font_size=1.1,
                        font_weight="bold",
                    ),
                    rio.Text(
                        "You made 169 sales this month.",
                        style=theme.TEXT_STYLE_DARKER_SMALL,
                    ),
                    align_y=0,
                    spacing=0.5,
                    margin_top=0.2,
                ),
                spacing=1,
                align_x=0,
                align_y=0,
            ),
            sales_info,
            spacing=1,
            margin=1,
        )

        # Style the content with a rectangle
        return rio.Rectangle(
            content=content,
            fill=rio.Color.TRANSPARENT,
            stroke_color=self.session.theme.neutral_color,
            stroke_width=0.1,
            corner_radius=self.session.theme.corner_radius_medium,
        )


# </component>
