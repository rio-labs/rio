from __future__ import annotations

import rio

# <additional-imports>
from .. import constants, theme

# </additional-imports>


# <component>
# Calculate the total sales by summing the values
total_sales = constants.COUNTRY_SALES_DATA.get_total_sales()


class CountryInfo(rio.Component):
    """
    A component that displays the country name and the sales amount.

    This component visually represents the sales percentage of a country using a
    progress bar and displays the country name, sales percentage, and a
    color-coded bar.

    ## Parameters

    `country`: The name of the country.

    `sales`: The sales amount for the country.

    `color`: The color associated with the country, used for the progress bar
    and text.

    `max_width`: The maximum width of the progress bar.
    """

    country: str
    sales: int
    color: str
    max_width: float = 60

    def build(self) -> rio.Component:
        # Calculate the sales percentage based on the total sales
        sales_percentage = (self.sales / total_sales) * 100

        return rio.Row(
            rio.Text(
                self.country,
                fill=rio.Color.from_hex(self.color),
                align_x=0,
                min_width=7.1,
            ),
            # Display the progress bar using a stack of rectangles
            rio.Stack(
                # Background bar (neutral color)
                rio.Rectangle(
                    fill=self.session.theme.neutral_color,
                    corner_radius=9999,
                ),
                # Foreground bar (color-coded based on the country)
                rio.Rectangle(
                    fill=rio.Color.from_hex(self.color),
                    corner_radius=9999,
                    min_width=(sales_percentage / 100) * self.max_width,
                    align_x=0,
                ),
                # Allow the bar to grow horizontally
                grow_x=True,
            ),
            rio.Text(
                f"{int(sales_percentage)} %",
                fill=theme.TEXT_FILL_DARKER,
                min_width=2.1,
                align_x=1,
            ),
            spacing=1,
            grow_x=True,
            margin_x=0.5,
        )


class TopCountriesCard(rio.Component):
    """
    A component that displays a card with the top countries by revenue.
    """

    def build(self) -> rio.Component:
        country_info = rio.Column(spacing=1)
        for country in constants.COUNTRY_SALES_DATA.countries:
            country_info.add(
                CountryInfo(country.name, country.sales, country.color),
            )

        content = rio.Column(
            rio.Row(
                rio.Icon(
                    "material/language:fill",
                    min_height=3.5,
                    min_width=3.5,
                ),
                rio.Column(
                    rio.Text(
                        "Top Countries",
                        font_size=1.1,
                        font_weight="bold",
                    ),
                    rio.Text(
                        "You made sales in 20 countries this month.",
                        style=theme.TEXT_STYLE_DARKER_SMALL,
                    ),
                    align_y=0,
                    spacing=0.5,
                    margin_top=0.2,
                ),
                spacing=1,
                align_y=0,
                align_x=0,
            ),
            country_info,
            spacing=1,
            margin=1,
        )
        return rio.Rectangle(
            content=content,
            fill=rio.Color.TRANSPARENT,
            # Add a Stroke to the rectangle
            stroke_color=self.session.theme.neutral_color,
            stroke_width=0.1,
            corner_radius=self.session.theme.corner_radius_medium,
        )


# </component>
