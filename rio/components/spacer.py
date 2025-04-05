from __future__ import annotations

import typing as t

from . import class_container
from .component import Key

__all__ = [
    "Spacer",
]


@t.final
class Spacer(class_container.ClassContainer):
    """
    An invisible component which grows by default.

    Spacers are invisible components which add empty space between other
    components. While similar effects can often be achieved using margins and
    alignment, code utilizing spacers can sometimes be easier to read.

    Note that unlike most components in Rio, `Spacer` does not have a `natural`
    size. Instead it defaults to a width and height of `grow`, as that is how
    they're most frequently used.


    ## Examples

    This example will display two texts in a Row, with one of them being pushed
    to the very left and the other to the very right:

    ```python
    rio.Row(
        rio.Text("Hello"),
        rio.Spacer(),
        rio.Text("World"),
    )
    ```
    """

    def __init__(
        self,
        *,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = True,
        grow_y: bool = True,
        key: Key | None = None,
    ) -> None:
        super().__init__(
            None,
            ["rio-spacer"],
            key=key,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
        )

    def _get_debug_details_(self) -> dict[str, t.Any]:
        result = super()._get_debug_details_()

        # Don't inherit the content from `rio.ClassContainer`.
        del result["content"]

        return result


# Make sure the component is recognized as `ClassContainer`, rather than a new
# component.
Spacer._unique_id_ = class_container.ClassContainer._unique_id_
