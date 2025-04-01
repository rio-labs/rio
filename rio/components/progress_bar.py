from __future__ import annotations

import typing as t

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "ProgressBar",
]


@t.final
class ProgressBar(FundamentalComponent):
    """
    A progress indicator in the shape of a horizontal bar.

    `ProgressBar` conveys to the user that activity is ongoing. It can either
    display the exact progress as a fraction from 0 to 1, or it can display an
    indeterminate progress animation, which is useful when the exact progress
    isn't known.

    The circular counterpart to this component is the `ProgressCircle`.


    ## Attributes

    `progress`: The progress to display, as a fraction from 0 to 1. If `None`,
        the progress indicator will be indeterminate.

    `color`: The color scheme of the progress indicator. Keeping the default
        is recommended, but it may make sense to change the color in
        case the default is hard to perceive on your background.

    `rounded`: Whether the corners of the progress bar should be rounded.

    ## Examples

    If you don't pass a value to `rio.ProgressBar`, it will play an animation to
    indicate that something is happening, without showing any specific progress:

    ```python
    rio.ProgressBar()
    ```

    Here's a more complete example, with a button that slowly fills up the
    progress bar:

    ```python
    class ProgressBarExample(rio.Component):
        working: bool = False
        progress: float = 0

        async def do_the_work(self):
            self.working = True

            # Simulate some work
            for p in range(10):
                await asyncio.sleep(1)

                # Update the progress
                self.progress = (p + 1) / 10

                # Tell rio to rebuild this component. Without this, the
                # ProgressBar wouldn't update until this function exits.
                self.force_refresh()

            self.working = False

        def build(self):
            return rio.Column(
                rio.Button(
                    "start working",
                    on_press=self.do_the_work,
                    # Make sure the button can't be pressed while we're busy
                    is_sensitive=not self.working,
                ),
                rio.ProgressBar(self.progress),
            )
    ```
    """

    progress: float | None
    color: rio.ColorSet
    rounded: bool

    def __init__(
        self,
        progress: float | None = None,
        *,
        color: rio.ColorSet = "keep",
        rounded: bool = True,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ):
        """
        ## Parameters

        `progress`: The progress to display, as a fraction from 0 to 1. If `None`,
            the progress indicator will be indeterminate.

        `color`: The color scheme of the progress indicator. Keeping the default
            is recommended, but it may make sense to change the color in case
            the default is hard to perceive on your background.


        `rounded`: Whether the corners of the progress bar should be rounded.
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
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
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
        self.rounded = rounded


ProgressBar._unique_id_ = "ProgressBar-builtin"
