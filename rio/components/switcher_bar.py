from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import Jsonable, JsonDoc

import rio

from .. import icon_registry
from ..self_serializing import SelfSerializing
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "SwitcherBarChangeEvent",
    "SwitcherBar",
    "SwitcherBarItem",
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


class SwitcherBarItem(t.Generic[T], SelfSerializing):
    def __init__(
        self,
        value: T,
        name: str | None = None,
        icon: str | None = None,
    ) -> None:
        if name is None:
            name = str(value)

        self.value = value
        self.name = name
        self.icon = icon

    def _serialize(self, sess: rio.Session) -> Jsonable:
        return {
            "name": self.name,
            "icon": self.icon,
        }


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

    `items`: The list of `SwicherBarItem`s to display.

    `color`: The color of the switcher bar.

    `orientation`: The orientation of the switcher bar.

    `spacing`: The spacing between options.

    `selected_value`: The currently selected value.

    `allow_none`: Whether the switcher bar can have no value selected.

    `on_change`: Triggered whenever the selected value changes.


    ## Examples

    In the simplest case, you can simply pass the values you want to display to
    the constructor:

    ```python
    rio.SwitcherBar(
        'foo',
        'bar',
        selected_value='bar',
    )
    ```

    For more control, use `rio.SwitcherBarItem`s:

    ```python
    rio.SwitcherBar(
        rio.SwitcherBarItem(1, "foo", icon="material/music_note"),
        rio.SwitcherBarItem(2, "bar", icon="material/castle"),
        selected_value=2,
    )
    ```

    You can use a `SwitcherBar` to create your own custom Navigation Bar. Use
    the `url_segment` defined in your `rio.App` and `rio.ComponentPage`
    instances to navigate to the selected page. Here is an example of a custom
    `NavigationBar` component:

    ```python
    class NavigationBar(rio.Component):
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
                        rio.SwitcherBarItem("/", "Home"),
                        rio.SwitcherBarItem("first-page", "First Page"),
                        rio.SwitcherBarItem("second-page", "Second Page"),
                        selected_value=self.session.active_page_instances[0].url_segment,
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

    items: list[SwitcherBarItem[T]]
    color: rio.ColorSet
    orientation: t.Literal["horizontal", "vertical"]
    spacing: float
    selected_value: T | None
    allow_none: bool
    on_change: rio.EventHandler[SwitcherBarChangeEvent[T]]

    @t.overload
    def __init__(
        self,
        *items: SwitcherBarItem[T] | T,
        color: rio.ColorSet = "keep",
        orientation: t.Literal["horizontal", "vertical"] = "horizontal",
        spacing: float = 1.0,
        allow_none: bool = False,
        selected_value: T | None = None,
        on_change: rio.EventHandler[SwitcherBarChangeEvent[T]] = None,
        key: Key | None = None,
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
        accessibility_role: AccessibilityRole | None = None,
    ):
        pass

    @t.overload
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
        key: Key | None = None,
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
        accessibility_role: AccessibilityRole | None = None,
    ):
        pass

    def __init__(
        self,
        *args: SwitcherBarItem[T] | T | t.Sequence[T],
        values: t.Sequence[T] | None = None,
        names: t.Sequence[str] | None = None,
        icons: t.Sequence[str | None] | None = None,
        color: rio.ColorSet = "keep",
        orientation: t.Literal["horizontal", "vertical"] = "horizontal",
        spacing: float = 1.0,
        allow_none: bool = False,
        selected_value: T | None = None,
        on_change: rio.EventHandler[SwitcherBarChangeEvent[T]] = None,
        key: Key | None = None,
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
        accessibility_role: AccessibilityRole | None = None,
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
            accessibility_role=accessibility_role,
        )

        if (
            values is not None
            or names is not None
            or icons is not None
            or (len(args) == 1 and isinstance(args[0], t.Sequence))
        ):
            if values is None:
                values = t.cast(t.Sequence[T], args[0])

            # Names default to the string representation of the values
            if names is None:
                names = [str(value) for value in values]
            elif len(names) != len(values):
                raise ValueError("`names` must be the same length as `values`.")

            if icons is None:
                icons = [None for _ in values]
            elif len(icons) != len(values):
                raise ValueError("`icons` must be the same length as `values`.")

            items = [
                SwitcherBarItem(value, name, icon)
                for value, name, icon in zip(values, names, icons)
            ]
        else:
            items = [
                arg
                if isinstance(arg, SwitcherBarItem)
                else SwitcherBarItem(arg)
                for arg in t.cast(tuple[SwitcherBarItem[T] | T, ...], args)
            ]

        if not items:
            raise ValueError("`SwitcherBar` must have at least one option.")

        # Make sure the icon names are valid
        for item in items:
            if item.icon is not None:
                icon_registry.get_icon_svg(item.icon)

        self.items = items
        self.selected_value = selected_value
        self.color = color
        self.orientation = orientation
        self.spacing = spacing
        self.allow_none = allow_none
        self.on_change = on_change

    def __post_init__(self) -> None:
        # Make sure a value is selected, if needed
        if self.selected_value is None and not self.allow_none:
            self.selected_value = self.items[0].value

    def _fetch_selected_name(self) -> str | None:
        # None is fine
        if self.selected_value is None:
            assert self.allow_none
            return None

        # The frontend works with names, not values. Get the corresponding name.

        # Avoid hammering a potential attribute binding
        selected_value = self.selected_value

        # Fetch the name
        for item in self.items:
            if item.value == selected_value:
                return item.name
        else:
            # If nothing matches, just select the first option
            return self.items[0].name

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "items": [item._serialize(self.session) for item in self.items],
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
            for item in self.items:
                if item.name == selected_name:
                    selected_value = item.value
                    break
            else:
                # Invalid names may be sent due to lag between the frontend and
                # backend. Ignore them.
                return

        self._apply_delta_state_from_frontend(
            {"selected_value": selected_value}
        )

        # Trigger the event
        await self.call_event_handler(
            self.on_change, SwitcherBarChangeEvent(selected_value)
        )


SwitcherBar._unique_id_ = "SwitcherBar-builtin"
