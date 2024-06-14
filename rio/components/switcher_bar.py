from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, final

from uniserde import JsonDoc

import rio

from ..icons import icon_registry
from .fundamental_component import FundamentalComponent

__all__ = [
    "SwitcherBarChangeEvent",
    "SwitcherBar",
]

T = TypeVar("T")


@final
@dataclass
class SwitcherBarChangeEvent(Generic[T]):
    value: T | None


@final
class SwitcherBar(FundamentalComponent, Generic[T]):
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
    page changes. Use the page_url defined in your rio.App and rio.Page
    instances to navigate to the selected page. Here is an example of a custom
    `NavigationBar` component:

    ```python
    class NavigationBar(rio.Component):
        # Make sure the navigation bar is updated, even if the user navigates
        # to another page by another means than the navbar itself.
        @rio.event.on_page_change
        async def _on_page_change(self) -> None:
            await self.force_refresh()

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
                        ].page_url,
                        align_y=0.5,
                        color="primary",
                        on_change=self.on_change,
                    ),
                    margin=1,
                    width="grow",
                ),
            )
    ```

    ## Metadata

    `experimental`: True
    """

    names: list[str]
    values: list[T]
    icon_svg_sources: list[str | None]
    color: rio.ColorSet
    orientation: Literal["horizontal", "vertical"]
    spacing: float
    selected_value: T | None
    allow_none: bool
    on_change: rio.EventHandler[SwitcherBarChangeEvent[T]]

    def __init__(
        self,
        values: list[T],
        *,
        names: list[str] | None = None,
        icons: Sequence[str | None] | None = None,
        color: rio.ColorSet = "keep",
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        spacing: float = 1.0,
        allow_none: bool = False,
        selected_value: T | None = None,
        on_change: rio.EventHandler[SwitcherBarChangeEvent[T]] = None,
        key: str | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        width: float | Literal["natural", "grow"] = "natural",
        height: float | Literal["natural", "grow"] = "natural",
        align_x: float | None = None,
        align_y: float | None = None,
    ):
        """
        ## Parameters

        `icons`: The list of icons to display along with with each name.
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
            width=width,
            height=height,
            align_x=align_x,
            align_y=align_y,
        )

        self.values = values
        self.color = color
        self.orientation = orientation
        self.spacing = spacing
        self.allow_none = allow_none
        self.on_change = on_change

        if not values:
            raise ValueError("`SwitcherBar` must have at least one option.")

        # Names default to the string representation of the values
        if names is None:
            self.names = [str(value) for value in values]
        else:
            if len(names) != len(values):
                raise ValueError("`names` must be the same length as `values`.")

            self.names = names

        # Icons default to `None`. Also, fetch their SVG sources so any errors
        # are raised now, rather than later.
        if icons is None:
            self.icon_svg_sources = [None] * len(values)
        else:
            if len(icons) != len(values):
                raise ValueError("`icons` must be the same length as `values`.")

            self.icon_svg_sources = [
                None if icon is None else icon_registry.get_icon_svg(icon)
                for icon in icons
            ]

        self.selected_value = selected_value

    def __post_init__(self) -> None:
        # Make sure a value is selected, if needed
        if self.selected_value is None and not self.allow_none:
            self.selected_value = self.values[0]

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

    def _custom_serialize(self) -> JsonDoc:
        result = {
            "optionNames": self.names,
            "optionIcons": self.icon_svg_sources,
            "selectedName": self._fetch_selected_name(),
            "color": self.session.theme._serialize_colorset(self.color),
        }

        return result

    async def _on_message(self, msg: Any) -> None:
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


SwitcherBar._unique_id = "SwitcherBar-builtin"
