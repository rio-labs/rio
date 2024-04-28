from __future__ import annotations

from typing import Literal, final

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "ProgressCircle",
]


@final
class ProgressCircle(FundamentalComponent):
    """
    A progress indicator in the shape of a circle.

    `ProgressCircle` conveys to the user that activity is ongoing. It can either
    display the exact progress as a fraction from 0 to 1, or it can display an
    indeterminate progress animation, which is useful when the exact progress
    isn't known.

    Note that unlike most components in Rio, `ProgressCircle` does not have a
    `natural` size, since the circle can easily be scaled to fit any size.
    Therefore it defaults to a reasonable size which should fit most use cases.

    The linear counterpart to this component is the `ProgressBar`.


    ## Attributes

    `progress`: The progress to display, as a fraction from 0 to 1. If `None`,
        the progress indicator will be indeterminate.

    `color`: The color scheme of the progress indicator. Keeping the default
        is recommended, but it may make sense to change the color in
        case the default is hard to perceive on your background.


    ## Examples

    A minimal example displaying a progress circle that is 50% complete.

    ```python
    rio.ProgressCircle(progress=0.5)
    ```
    """

    progress: float | None
    color: rio.ColorSet

    def __init__(
        self,
        *,
        progress: float | None = None,
        color: rio.ColorSet = "keep",
        size: float | Literal["grow"] = 3.5,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        align_x: float | None = None,
        align_y: float | None = None,
    ):
        """
        ## Parameters
            progress: The progress to display, as a fraction from 0 to 1. If `None`,
                the progress indicator will be indeterminate.

            color: The color scheme of the progress indicator. Keeping the default
                is recommended, but it may make sense to change the color in case
                the default is hard to perceive on your background.

            size: The size of the progress indicator. This is equivalent to setting
                a component's `width` and `height` to the same value.

                Note that unlike most components in Rio, `ProgressCircle` does not
                have a `natural` size, since the circle can easily be scaled to fit
                any size. Therefore it defaults to a reasonable size which should
                fit most use cases.
        """
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            width=size,
            height=size,
            align_x=align_x,
            align_y=align_y,
        )

        self.progress = progress
        self.color = color


ProgressCircle._unique_id = "ProgressCircle-builtin"
