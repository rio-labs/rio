import rio

# <additional-imports>
from .. import theme

# </additional-imports>


# <component>
class ToggleGroup(rio.Component):
    """
    A toggle group component that allows users to switch between two states.

    This component provides a toggle switch with a heading and subheading. Users
    can toggle the switch by clicking anywhere on the rectangle, not just on the
    switch itself.


    ## Attributes:

    `heading`: The main heading for the toggle group.

    `sub_heading`: The sub heading or description for the toggle group.

    `is_on`: A boolean value indicating whether the toggle group is currently
    turned on or off.
    """

    heading: str
    sub_heading: str

    is_on: bool = True

    def _on_press(self, _: rio.PointerEvent) -> None:
        # Toggle the switch state
        self.is_on = not self.is_on

    def build(self) -> rio.Component:
        return rio.PointerEventListener(
            # The clickable rectangle
            rio.Rectangle(
                content=rio.Row(
                    # Column for the heading and subheading
                    rio.Column(
                        rio.Text(
                            self.heading,
                            font_weight="bold",
                        ),
                        rio.Text(
                            self.sub_heading,
                            fill=theme.TEXT_FILL_DARKER,
                            font_size=0.9,
                        ),
                        grow_x=True,
                    ),
                    rio.Switch(is_on=self.bind().is_on),
                ),
                fill=rio.Color.TRANSPARENT,
                cursor="pointer",
            ),
            on_press=self._on_press,
        )


# </component>
