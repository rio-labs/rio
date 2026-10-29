import rio

# <additional-imports>
from .. import theme

# </additional-imports>


# <component>
class ContentColumn(rio.Component):
    """
    Displays a column containing a main text, optional support text, and an
    indicator for required fields.


    ## Attributes:

    `text`: The main text to display.

    `support_text`: The support text to display below the main text.

    `is_required`: A boolean indicating whether the field is required. If
    `True`, a red asterisk will be displayed next to the main text.
    """

    text: str
    support_text: str
    is_required: bool = False

    def build(self) -> rio.Component:
        # Create a column to hold the text and support text
        content_column = rio.Column(spacing=0.5, grow_x=True)

        # Add the main text
        content_row = rio.Row(
            rio.Text(
                self.text,
                font_weight="bold",
                fill=theme.TEXT_FILL_BRIGHTER,
            ),
            spacing=0.1,
            align_x=0,
        )

        # Add a red asterisk if the field is required
        if self.is_required:
            content_row.add(
                rio.Text(
                    "*",
                    font_size=self.session.theme.text_style.font_size * 0.8,
                    fill=rio.Color.RED,
                    align_y=0,
                )
            )

        # Add the text row to the column
        content_column.add(content_row)

        # Add support text
        content_column.add(
            rio.Text(
                self.support_text,
                style=theme.TEXT_STYLE_DARKER_SMALL,
            )
        )

        return content_column


class ContentContainer(rio.Component):
    """
    A container component that displays a labeled section with optional support
    text, an additional component on the right, and an optional separator.


    ## Attributes:

    `text`: The main text to display.

    `support_text`: The support text to display below the main text.

    `is_required`: A boolean indicating whether the field is required. If
    `True`, a red asterisk will be displayed next to the main text.

    `content_right`: An optional component to display on the right side of the
    container.

    `add_separator`: A boolean indicating whether to add a separator below the
    container.
    """

    text: str
    support_text: str
    is_required: bool = False
    content_right: rio.Component | None = None
    add_separator: bool = True

    def build(self) -> rio.Component:
        content_row = rio.Row(margin_bottom=1.5)

        content_row.add(
            ContentColumn(
                self.text,
                self.support_text,
                self.is_required,
            )
        )

        # Add the right content if provided
        if self.content_right:
            content_row.add(self.content_right)

        # Add a separator if specified
        if self.add_separator:
            return rio.Column(
                content_row,
                rio.Separator(color=self.session.theme.neutral_color),
            )

        # Return the content row without a separator
        return content_row


# </component>
