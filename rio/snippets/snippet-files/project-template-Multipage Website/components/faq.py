# <additional-imports>
import rio

from .. import data_models, theme

# </additional-imports>


# <component>
class Faq(rio.Component):
    """
    A responsive FAQ component that toggles the visibility of an answer.

    The component includes:
    - A header that serves as a clickable question.
    - A body that displays the answer when expanded.
    - An open/close icon to indicate the state.


    ## Attributes:

    `header`: The question or title of the FAQ item.

    `body`: The answer or description associated with the FAQ.

    `is_last`: Indicates if this is the last FAQ item in a list for additional
    spacing.

    `is_open`: Determines whether the FAQ item is expanded or collapsed.
    """

    header: str
    body: str
    is_last: bool = False
    is_open: bool = True

    def _on_toggle(self, _: rio.PointerEvent) -> None:
        """
        Toggles the `is_open` state when the FAQ header is clicked.
        """
        self.is_open = not self.is_open

    def build(self) -> rio.Component:
        # Get the current device from the session
        device = self.session[data_models.PageLayout].device
        # Specify margin_y to add space between header and body
        margin_y = 1.8

        # Define the icon and content based on the open state
        if self.is_open:
            icon = rio.Icon(
                "material/keyboard_arrow_down",  # Down arrow when expanded
                min_height=1.5,
                min_width=1.5,
                align_x=1,  # Align icon to the right
            )
            # Column to hold answer and separators
            content = rio.Column()
            # Add a separator above the body
            content.add(
                rio.Separator(
                    color=theme.NEUTRAL_COLOR_BRIGHTER,
                ),
            )
            # Add the body text
            content.add(
                rio.Container(
                    rio.Text(
                        self.body,
                        style=theme.DARKER_TEXT,
                        overflow="wrap",
                        margin_y=margin_y,
                    ),
                ),
            )
            # Add a separator if this is the last FAQ for better spacing
            if self.is_last:
                content.add(
                    rio.Separator(color=theme.NEUTRAL_COLOR_BRIGHTER),
                )

        else:
            icon = rio.Icon(
                "material/chevron_right",  # Right arrow when collapsed
                min_height=1.5,
                min_width=1.5,
                align_x=1,  # Align icon to the right
            )
            # No content displayed when collapsed
            content = None

        # Construct the header row with pointer interaction
        return rio.Column(
            rio.PointerEventListener(
                rio.Rectangle(
                    content=rio.Row(
                        rio.Text(
                            self.header,
                            font_weight="bold",
                            # Adjust font size for device
                            font_size=1.2 if device == "desktop" else 1.1,
                            selectable=False,  # Prevent text selection
                        ),
                        icon,  # Add the toggle icon
                        margin_y=margin_y,  # Add vertical margin
                    ),
                    fill=rio.Color.TRANSPARENT,
                    # Set pointer cursor for interactivity
                    cursor="pointer",
                ),
                on_press=self._on_toggle,
            ),
            # Add a switcher to toggle the visibility of the content
            rio.Switcher(
                content=content,
                transition_time=0.2,
            ),
        )


# </component>
