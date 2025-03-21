import enum

from . import deprecations

__all__ = ["CursorStyle"]


@deprecations.deprecated(
    since="0.11.3",
    description="`CursorStyle` is deprecated in favor of string literals.",
)
class CursorStyle(enum.Enum):
    """
    Enumeration of all available cursor styles. Use these to indicate which
    kinds of action a user can perform while hovering over a component.

    ## Example

    ```python
    rio.Rectangle(
        fill=rio.Color.WHITE,
        cursor=rio.CursorStyle.POINTER,
    )
    ```
    """

    DEFAULT = enum.auto()
    NONE = enum.auto()
    HELP = enum.auto()
    POINTER = enum.auto()
    LOADING = enum.auto()  # "wait" in CSS
    BACKGROUND_LOADING = enum.auto()  # "progress" in CSS
    CROSSHAIR = enum.auto()
    TEXT = enum.auto()
    MOVE = enum.auto()
    NOT_ALLOWED = enum.auto()
    CAN_GRAB = enum.auto()  # "grab" in CSS
    IS_GRABBED = enum.auto()  # "grabbing" in CSS
    ZOOM_IN = enum.auto()
    ZOOM_OUT = enum.auto()
