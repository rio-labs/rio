from __future__ import annotations

# <additional-imports>
import rio

# </additional-imports>


# <component>
class FakeLink(rio.Component):
    """
    A styled component resembling a hyperlink.

    This component is designed to visually appear like a link but does not have
    any associated functionality or navigation.


    ## Attributes:

    `text`: The text to display as the link.
    """

    text: str

    def build(self) -> rio.Component:
        """
        Constructs the fake link component.

        The component includes:
        - Text styled to resemble a hyperlink.
        - A pointer cursor on hover for visual feedback.
        """
        return rio.Rectangle(
            content=rio.Text(
                text=self.text,
                font_size=0.9,
            ),
            cursor="pointer",
            fill=self.session.theme.background_color,
            align_x=0,
        )


# </component>
