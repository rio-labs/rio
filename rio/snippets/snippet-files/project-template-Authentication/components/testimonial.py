from __future__ import annotations

import rio


# <component>
class Testimonial(rio.Component):
    """
    Displays 100% legitimate testimonials from real, most definitely not made-up
    people.
    """

    # The quote somebody has definitely said about this company.
    quote: str

    # Who said the quote, probably Mark Twain.
    name: str

    # The company the person is from.
    company: str

    def build(self) -> rio.Component:
        # Wrap everything in a card to make it stand out from the background.
        return rio.Card(
            # A second card, but this one is offset a bit. This allows the outer
            # card to pop out a bit, displaying a nice colorful border at the
            # bottom.
            rio.Card(
                # Combine the quote, name, and company into a column.
                rio.Column(
                    rio.Markdown(self.quote),
                    rio.Text(
                        f"— {self.name}",
                        justify="left",
                    ),
                    rio.Text(
                        f"{self.company}",
                        # Dim text and icons are used for less important
                        # information and make the app more visually appealing.
                        style="dim",
                        justify="left",
                    ),
                    spacing=0.4,
                    margin=2,
                    align_y=0.5,
                ),
                margin_bottom=0.2,
            ),
            # Important colors such as primary, secondary, neutral and
            # background are available as string constants for easy access.
            color="primary",
            min_width=20,
        )


# </component>
