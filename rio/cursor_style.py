import enum

__all__ = ["CursorStyle"]


class CursorStyle(enum.Enum):
    """
    Enumeration of all available cursor styles. Use these to indicate which
    kinds of action a user can perform while hovering over a component.
    """

    # TODO: Extend these
    DEFAULT = enum.auto()
    POINTER = enum.auto()
