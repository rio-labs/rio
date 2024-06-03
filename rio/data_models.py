from dataclasses import dataclass


@dataclass
class ComponentLayout:
    """
    Stores information about a component's layout. This includes the position
    and size that was actually allocated, rather than just requested.
    """

    # The component's position relative to the top-left corner of the viewport
    left_in_viewport: float
    top_in_viewport: float

    # The component's position relative to the top-left corner of the parent
    left_in_parent: float
    top_in_parent: float

    # How much space the component has requested
    natural_width: float
    natural_height: float

    # How much space the component was actually allocated
    allocated_width: float
    allocated_height: float
