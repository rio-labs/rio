import rio

# <component>
LOGO_ASPECT_RATIO = 1.75 / 2.5
LOGO_FONT_ASPECT_RATIO = 24.667 / 16
LOGO_UNIT_RATIO = 0.625


class RioLogo(rio.Component):
    """
    A component that renders the Rio logo alongside the text "Rio".


    ## Attributes:

    `min_height`: The minimum height of the logo.

    `text_size`: The size of the "Rio" text.

    `spacing`: Spacing between the logo and the text.

    `logo_fill`: The color of the "Rio" text.
    """

    min_height: float = 4
    text_size: float = 1
    spacing: float = 1
    logo_fill: rio.Color | None = None

    def build(self) -> rio.Component:
        return rio.Row(
            rio.Icon(
                "rio/logo:color",
                min_width=self.min_height * LOGO_ASPECT_RATIO * LOGO_UNIT_RATIO,
                min_height=self.min_height * LOGO_UNIT_RATIO,
            ),
            rio.Text(
                "Rio",
                font_size=self.text_size * LOGO_FONT_ASPECT_RATIO,
                fill=(
                    self.session.theme.heading1_style.fill
                    if self.logo_fill is None
                    else self.logo_fill
                ),
            ),
            spacing=self.spacing * LOGO_UNIT_RATIO,
            align_x=0.5,
            align_y=0.5,
        )


# </component>
