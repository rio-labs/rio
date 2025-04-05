from __future__ import annotations

import typing as t

import rio

from .. import deprecations
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "ProgressCircle",
]


@t.final
@deprecations.component_kwarg_renamed(
    since="0.10",
    old_name="size",
    new_name="min_size",
)
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

    Here's a minimal example displaying a progress circle that is 40% complete:

    ```python
    rio.ProgressCircle(progress=0.4)
    ```

    You don't have to pass any progress to `rio.ProgressCircle`. If you don't,
    it will indicate to the user that something is happening, without showing
    any specific progress.

    ```python
    rio.ProgressCircle()
    ```
    """

    progress: float | None
    color: rio.ColorSet

    def __init__(
        self,
        progress: float | None = None,
        *,
        color: rio.ColorSet = "keep",
        min_size: float = 3.5,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
        """
        ## Parameters

        `progress`: The progress to display, as a fraction from 0 to 1. If
            `None`, the progress indicator will be indeterminate.

        `color`: The color scheme of the progress indicator. Keeping the default
            is recommended, but it may make sense to change the color in case
            the default is hard to perceive on your background.

        `min_size`: The size of the progress indicator. This is equivalent to
            setting a component's `width` and `height` to the same value.

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
            min_width=min_size,
            min_height=min_size,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        self.progress = progress
        self.color = color


ProgressCircle._unique_id_ = "ProgressCircle-builtin"
