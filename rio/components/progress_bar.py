from typing import final

from .fundamental_component import FundamentalComponent

__all__ = [
    "ProgressBar",
]


@final
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


    ## Examples

    A minimal example displaying a progress bar that is 40% complete.

    ```python
    rio.ProgressBar(progress=0.4)
    ```

    You don't have to pass any progress to `rio.ProgressBar`. If you don't,
    it will indicate to the user that something is happening, without showing
    any specific progress.

    ```python
    rio.ProgressBar()
    ```
    """

    progress: float | None = None


ProgressBar._unique_id = "ProgressBar-builtin"
