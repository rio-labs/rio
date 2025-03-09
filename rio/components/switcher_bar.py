from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .. import icon_registry
from .fundamental_component import FundamentalComponent

__all__ = [
    "SwitcherBarChangeEvent",
    "SwitcherBar",
]

T = t.TypeVar("T")


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class SwitcherBarChangeEvent(t.Generic[T]):
    """
    Holds information regarding a switcher bar change event.

    This is a simple dataclass that stores useful information for when the user
    interacts with a switcher bar. You'll typically receive this as argument in
    `on_change` events.

    ## Attributes

    `value`: The new value of the `SwitcherBar`.
    """

    value: T | None


@t.final
class SwitcherBar(FundamentalComponent, t.Generic[T]):
    """
    Displays a series of options and allows the user to switch between them.

    A `SwitcherBar` displays a list of options and allows the user to select one
    of them. Each option has a name, value and optionally an icon. The selected
    option is highlighted and can be changed by the user.

    Normally exactly one value is selected at all times. If `allow_none` is
    `True`, the user can also select no option at all. In this case, the
    `selected_value` will be `None`.


    ## Attributes

    `values`: The list of values which can be selected.

    `names`: The list of names to display for each value. If `None`, the
        string representation of each value is used.

    `icons`: Optionally, a list of icons that should be displayed next to the
        names.

    `color`: The color of the switcher bar.

    `orientation`: The orientation of the switcher bar.

    `spacing`: The spacing between options.

    `selected_value`: The currently selected value.

    `allow_none`: Whether the switcher bar can have no value selected.

    `on_change`: Triggered whenever the selected value changes.


    ## Examples

    A simple switcher bar with three options:

    ```python
    rio.SwitcherBar(
        values=[1, 2, 3],
        names=["A-SwitchName", "B-SwitchName", "C-SwitchName"],
        selected_value=1,
        on_change=lambda event: print(event.value),
    )
    ```

    You can use a `SwitcherBar` to create your own custom Navigation Bar. use
    the on_page_change event to trigger a refresh of the `SwitcherBar` when the
    page changes. Use the `url_segment` defined in your `rio.App` and
    `rio.ComponentPage` instances to navigate to the selected page. Here is an
    example of a custom `NavigationBar` component:

    ```python
    class NavigationBar(rio.Component):
        # Make sure the navigation bar is updated, even if the user navigates
        # to another page by another means than the navbar itself.
        @rio.event.on_page_change
        def _on_page_change(self) -> None:
            self.force_refresh()

        def on_change(self, event: rio.SwitcherBarChangeEvent) -> None:
            # The user has selected a new value. Navigate to the corresponding
            # page.
            assert isinstance(event.value, str)
            self.session.navigate_to(event.value)

        def build(self) -> rio.Component:
            return rio.Card(
                rio.Row(
                    rio.Spacer(),
                    rio.SwitcherBar(
                        # For the values, we'll use the URL segments of the
                        # pages in the app. This makes it easy to navigate
                        # to them.
                        values=["/", "first-page", "second-page"],
                        names=["Home", "First Page", "Second Page"],
                        selected_value=self.session.active_page_instances[
                            0
                        ].url_segment,
                        align_y=0.5,
                        color="primary",
                        on_change=self.on_change,
                    ),
                    margin=1,
                    grow_x=True,
                ),
            )
    ```
    """

    names: t.Sequence[str]
    values: t.Sequence[T]
    icons: t.Sequence[str | None] | None
    color: rio.ColorSet
    orientation: t.Literal["horizontal", "vertical"]
    spacing: float
    selected_value: T | None
    allow_none: bool
    on_change: rio.EventHandler[SwitcherBarChangeEvent[T]]

    def __init__(
        self,
        values: t.Sequence[T],
        *,
        names: t.Sequence[str] | None = None,
        icons: t.Sequence[str | None] | None = None,
        color: rio.ColorSet = "keep",
        orientation: t.Literal["horizontal", "vertical"] = "horizontal",
        spacing: float = 1.0,
        allow_none: bool = False,
        selected_value: T | None = None,
        on_change: rio.EventHandler[SwitcherBarChangeEvent[T]] = None,
        key: str | int | None = None,
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
    ):
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
        )

        # Names default to the string representation of the values
        if names is None:
            names = [str(value) for value in values]

        self.names = names
        self.values = values
        self.icons = icons
        self.selected_value = selected_value
        self.color = color
        self.orientation = orientation
        self.spacing = spacing
        self.allow_none = allow_none
        self.on_change = on_change

    def __post_init__(self) -> None:
        values = self.values

        if not values:
            raise ValueError("`SwitcherBar` must have at least one option.")

        if len(self.names) != len(values):
            raise ValueError("`names` must be the same length as `values`.")

        # Icons
        icons = self.icons

        if icons is not None:
            if len(icons) != len(values):
                raise ValueError("`icons` must be the same length as `values`.")

            # Make sure the icon names are valid
            for icon in icons:
                if icon is not None:
                    icon_registry.get_icon_svg(icon)

        # Make sure a value is selected, if needed
        if self.selected_value is None and not self.allow_none:
            self.selected_value = values[0]

    def _fetch_selected_name(self) -> str | None:
        # None is fine
        if self.selected_value is None:
            assert self.allow_none
            return None

        # The frontend works with names, not values. Get the corresponding name.

        # Avoid hammering a potential attribute binding
        selected_value = self.selected_value

        # Fetch the name
        for name, value in zip(self.names, self.values):
            if value == selected_value:
                return name
        else:
            # If nothing matches, just select the first option
            return self.names[0]

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "selectedName": self._fetch_selected_name(),
        }

    async def _on_message_(self, msg: t.Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg

        # The frontend works with names, not values. Get the corresponding
        # value.
        selected_name = msg["name"]

        if selected_name is None:
            # Invalid names may be sent due to lag between the frontend and
            # backend. Ignore them.
            if not self.allow_none:
                return

            selected_value = None

        else:
            for name, value in zip(self.names, self.values):
                if name == selected_name:
                    selected_value = value
                    break
            else:
                # Invalid names may be sent due to lag between the frontend and
                # backend. Ignore them.
                return

        # TEMP, for debugging the switcher bar JS code
        # self._apply_delta_state_from_frontend({'selected_value': selected_value})
        self.selected_value = selected_value

        # Trigger the event
        await self.call_event_handler(
            self.on_change, SwitcherBarChangeEvent(self.selected_value)
        )

        # Refresh the session
        await self.session._refresh()


SwitcherBar._unique_id_ = "SwitcherBar-builtin"
