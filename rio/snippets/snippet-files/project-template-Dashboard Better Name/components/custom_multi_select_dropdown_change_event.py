# from __future__ import annotations

# import dataclasses
# import functools
# import typing as t

# import rio

# T = t.TypeVar("T")


# @dataclasses.dataclass
# class MultiSelectDropdownChangeEvent(t.Generic[T]):
#     """
#     Holds information regarding a dropdown change event.

#     This is a simple dataclass that stores useful information for when the user
#     selects an option in a `Dropdown`. You'll typically receive this as argument
#     in `on_change` events.

#     ## Attributes

#     `value`: The new `selected_value` of the `Dropdown`.
#     """

#     values: list[T]
