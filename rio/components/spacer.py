from __future__ import annotations

from typing import *  # type: ignore

from . import class_container

__all__ = [
    "Spacer",
]


@final
class Spacer(class_container.ClassContainer):
    """
    Adds empty space.

    Spacers are invisible components which add empty space between other
    components. While similar effects can often be achieved using margins and
    alignment, code with spacers can sometimes be easier to read.

    Note that unlike most components in Rio, `Spacer` does not have a `natural`
    size. Therefore it defaults to a width and height of `grow`, as that is how
    they're frequently used.


    ## Examples

    A minimal example of `Spacer` will be shown:

    ```python
    rio.Spacer(height=5)
    ```
    """

    def __init__(
        self,
        *,
        width: float | Literal["grow"] = "grow",
        height: float | Literal["grow"] = "grow",
        key: str | None = None,
    ):
        """
        ## Parameters
            width: How much space the spacer should take up horizontally.
            height: How much space the spacer should take up vertically.
        """

        super().__init__(
            None,
            ["rio-spacer"],
            key=key,
            width=width,
            height=height,
        )


# Make sure the component is recognized as `ClassContainer`, rather than a new
# component.
Spacer._unique_id = class_container.ClassContainer._unique_id
