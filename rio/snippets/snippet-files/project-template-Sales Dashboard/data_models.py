from __future__ import annotations

import dataclasses
import typing as t


@dataclasses.dataclass
class PageLayout:
    """
    Represents the layout configuration for a page.


    ## Attributes:

    `device`: Specifies the type of device for the page layout.

    `app_margin`: The margin of the app.

    `grow_x_content`: Whether the content should grow in the x direction.

    `grow_y_content`: Whether the content should grow in the y direction.

    `margin_in_card`: The margin of the card.

    `min_width_content`: The minimum width of the content.
    """

    device: t.Literal["desktop", "mobile"]
    margin_app: float
    grow_x_content: bool
    grow_y_content: bool
    margin_in_card: float
    min_width_content: float = 0
