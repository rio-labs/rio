from __future__ import annotations

import dataclasses
import math
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "Slider",
    "SliderChangeEvent",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class SliderChangeEvent:
    """
    Holds information regarding a slider change event.

    This is a simple dataclass that stores useful information for when the user
    switches changes the value of a `Slider`. You'll typically receive this as
    argument in `on_change` events.

    ## Attributes

    `value`: The new value of the slider.
    """

    value: float


@t.final
class Slider(FundamentalComponent):
    """
    A component for selecting a single number from a range.

    The `Slider` components allows the user to select a single real number value
    by dragging a handle along a line. The value can be any number within a
    range you can specify.


    ## Attributes

    `minimum`: The minimum value the slider can be set to.

    `maximum`: The maximum value the slider can be set to.

    `value`: The current value of the slider.

    `step`: The step size between slider values.

    `is_sensitive`: Whether the slider should respond to user input.

    `show_values`: Whether to display labels on the slider.

    `on_change`: A callback that is called when the value of the slider changes.


    ## Examples

    You can easily bind attributes track changes. If you want to make your
    `Slider` more responsive, you can easily achieve this by adding a lambda
    function call to on_change:

    ```python
    class MyComponent(rio.Component):
        value: int = 0

        def build(self) -> rio.Component:
            return rio.Slider(
                value=self.bind().value,  # Attribute binding
                minimum=0,
                maximum=100,
                step=1,
                show_values=True,
                on_change=lambda event: print(f"value: {event.value}"),
            )
    ```

    You can also use a method for updating the input value and do whatever you
    want. Note that methods are handy if you want to do more than just updating
    the input value. For example run async code or update other components based
    on the input text:

    ```python
    class MyComponent(rio.Component):
        value: float = 0

        def on_change(self, event: rio.SliderChangeEvent):
            self.value = event.value
            print(f"value: {self.value}")

        def build(self) -> rio.Component:
            return rio.Slider(
                value=self.value,
                minimum=0,
                maximum=100,
                step=1,
                show_values=True,
                on_change=self.on_change,
            )
    ```
    """

    minimum: float
    maximum: float
    value: float
    step: float
    is_sensitive: bool
    show_values: bool
    on_change: rio.EventHandler[SliderChangeEvent]

    def __init__(
        self,
        *,
        minimum: float = 0,
        maximum: float = 1,
        step: float = 0,
        value: float = 0.5,
        is_sensitive: bool = True,
        show_values: bool = False,
        on_change: rio.EventHandler[SliderChangeEvent] = None,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 1.3,
        min_height: float = 1.3,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
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

        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.value = value
        self.is_sensitive = is_sensitive
        self.show_values = show_values
        self.on_change = on_change

    def __post_init__(self) -> None:
        # Don't hammer potential attribute bindings
        minimum = self.minimum
        maximum = self.maximum
        step = self.step
        value = self.value

        initial_value = value

        if maximum <= minimum:
            raise ValueError(
                f"`maximum` must be greater than `minimum`. Got {maximum} <= {minimum}"
            )

        if step < 0:
            raise ValueError(
                f"`step` must be greater than or equal to 0. Got {step}"
            )

        if step != 0:
            value = round(value / step) * step

        value = min(maximum, max(minimum, value))

        # Only assign the value if it has in fact changed, as this causes a
        # refresh. If the value is bound to the parent and the parent rebuilds
        # this creates an infinite loop.
        if not math.isclose(value, initial_value):
            self.value = value

    # TODO: When `minimum` or `maximum` is changed, make sure the value is still
    # within the range

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"value"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

        if "value" in delta_state and not self.is_sensitive:
            raise AssertionError(
                f"Frontend tried to set `Slider.value` even though `is_sensitive` is `False`"
            )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        # Trigger on_change event
        try:
            new_value = delta_state["value"]
        except KeyError:
            pass
        else:
            assert isinstance(new_value, (int, float)), new_value
            await self.call_event_handler(
                self.on_change,
                SliderChangeEvent(new_value),
            )


Slider._unique_id_ = "Slider-builtin"
