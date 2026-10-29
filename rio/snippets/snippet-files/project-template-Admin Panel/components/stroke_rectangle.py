import typing as t

import rio

# <additional-imports>
from .. import theme

# </additional-imports>


# <component>
CursorStyle = t.Literal[
    "default",
    "none",
    "help",
    "pointer",
    "loading",  # "wait" in CSS
    "background-loading",  # "progress" in CSS
    "crosshair",
    "text",
    "move",
    "not-allowed",
    "can-grab",  # "grab" in CSS
    "grabbed",  # "grabbing" in CSS
    "zoom-in",
    "zoom-out",
]


class StrokeRectangle(rio.Component):
    """
    A rectangle with a stroke around it.

    Removes unnecessary boilerplate when creating rectangles with a stroke.


    ## Attributes:

    `content`: The content of the rectangle

    `corner_radius`: The corner radius of the rectangle

    `hover_fill`: The fill color of the rectangle when hovered

    `cursor`: The cursor style of the rectangle
    """

    content: rio.Component
    corner_radius: float = theme.THEME.corner_radius_small
    hover_fill: rio.Color | None = None
    cursor: CursorStyle = "default"

    def build(self) -> rio.Component:
        return rio.Rectangle(
            content=self.content,
            fill=self.session.theme.background_color,
            hover_fill=self.hover_fill,
            corner_radius=self.corner_radius,
            stroke_width=0.1,
            stroke_color=self.session.theme.neutral_color,
            cursor=self.cursor,
            transition_time=0.1,
        )


# </component>
