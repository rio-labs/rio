from __future__ import annotations

import dataclasses
import functools
import typing as t

import rio

T = t.TypeVar("T")


@dataclasses.dataclass
class MultiSelectDropdownChangeEvent(t.Generic[T]):
    """
    Holds information regarding a dropdown change event.

    This is a simple dataclass that stores useful information for when the user
    selects an option in a `Dropdown`. You'll typically receive this as argument
    in `on_change` events.

    ## Attributes

    `value`: The new `selected_value` of the `Dropdown`.
    """

    values: list[T]


class DropdownElement(rio.Component):
    """
    A custom component to display a rectangle with text and an icon.

    The option can be selected and deselected.


    ## Attributes:

    `name`: The name of the option.

    `is_selected`: A boolean indicating whether the option is selected.
    """

    name: str
    is_selected: bool = False

    on_press: rio.EventHandler[[]] = None

    async def _on_press(self, _: rio.PointerEvent) -> None:
        await self.call_event_handler(self.on_press)

    def build(self) -> rio.Component:
        # Change the fill color of the icon based on the selection state
        if self.is_selected:
            fill = self.session.theme.primary_color
        else:
            fill = rio.Color.TRANSPARENT

        # Create the content of the dropdown element
        content = rio.Row(
            rio.Text(
                self.name,
                selectable=False,
                font_weight="bold",
                grow_x=True,
            ),
            rio.Icon(
                "material/check",
                fill=fill,
                align_y=0.5,
                min_width=1.2,
                min_height=1.2,
            ),
            margin=0.5,
            spacing=0.5,
            min_height=1.2,
        )

        # Styling the dropdown element
        return rio.PointerEventListener(
            rio.Rectangle(
                content=content,
                fill=rio.Color.TRANSPARENT,
                hover_fill=self.session.theme.background_color,
                corner_radius=self.session.theme.corner_radius_small,
                transition_time=0.1,
                cursor="pointer",
            ),
            on_press=self._on_press,
        )


class PopupRectangle(rio.Component, t.Generic[T]):
    # Design Body of Popup/Dropdown
    options: t.Mapping[str, T] | t.Sequence[T]
    # options: list[t.Tuple[str, T]]
    selected_values: list[T]

    on_change_option: rio.EventHandler[[str | T]] = None

    async def _on_change_option(self, option: str | T) -> None:
        await self.call_event_handler(self.on_change_option, option)
        self.force_refresh()

    def build(self) -> rio.Component:
        content = rio.Column(margin=0.5, spacing=0.5)

        # Populate dropdown content based on whether options is a Mapping or Sequence
        if isinstance(self.options, t.Mapping):
            for option_key, option_value in self.options.items():
                content.add(
                    DropdownElement(
                        name=option_key,  # Use the key as the display name
                        is_selected=option_value in self.selected_values,
                        on_press=functools.partial(
                            self._on_change_option, option_key
                        ),
                    ),
                )
        else:  # self.options is a Sequence
            for option_value in self.options:
                content.add(
                    DropdownElement(
                        name=str(
                            option_value
                        ),  # Use the value's string representation as the name
                        is_selected=option_value in self.selected_values,
                        on_press=functools.partial(
                            self._on_change_option, option_value
                        ),
                    ),
                )

        # Styling the popup
        return rio.Rectangle(
            content=content,
            fill=self.session.theme.neutral_color,
            stroke_width=0.1,
            stroke_color=self.session.theme.neutral_color.brighter(0.2),
            corner_radius=self.session.theme.corner_radius_small,
            transition_time=0.1,
            align_x=0.5,
        )


# GO TO: t.Mapping[str, T] DELETE t.Sequence[T]
class MultiSelectDropdown(rio.Component, t.Generic[T]):
    label: str
    label_icon: str
    # Add KW only if it makes sense
    options: t.Mapping[str, T] | t.Sequence[T]
    selected_values: list[T] = []
    styling_color: rio.Color = rio.Color.GRAY
    user_closable: bool = True
    alignment: float = 0.5
    gap: float = 0.8  # TODO delete this

    is_open: bool = False

    on_change: rio.EventHandler[MultiSelectDropdownChangeEvent[T]] = None

    def on_change_option(self, option_key_or_value: str | T) -> None:
        """
        Toggle the selection of the option. Handles both Mapping and Sequence cases.
        """
        # Handle Mapping[str, T]
        if isinstance(self.options, t.Mapping):
            assert isinstance(option_key_or_value, str)
            option_value = self.options[option_key_or_value]

        # Handle Sequence[T]
        else:
            option_value = t.cast(T, option_key_or_value)

        # Update the selected values based on the option's current selection
        # state
        if option_value in self.selected_values:
            self.selected_values.remove(option_value)
        else:
            self.selected_values.append(option_value)

        # Rio automatically detects assignments to the components attributes.
        # However, since we've modified the attributes in-place without any
        # assignments we have to manually force a refresh.
        self.force_refresh()

    def on_press(self, _: rio.PointerEvent) -> None:
        self.is_open = not self.is_open

    def build(self) -> rio.Component:
        return rio.Popup(
            anchor=rio.PointerEventListener(
                # Design Header of Dropdown
                rio.Rectangle(
                    content=rio.Row(
                        rio.Icon(
                            self.label_icon,
                            fill=self.styling_color,
                            align_y=0.5,
                            min_width=1.2,
                            min_height=1.2,
                        ),
                        rio.Text(
                            self.label,
                            selectable=False,
                            fill=self.styling_color,
                        ),
                        rio.Icon(
                            "material/keyboard_arrow_down",
                            fill=self.styling_color,
                            align_y=0.5,
                        ),
                        spacing=0.5,
                        align_y=0.5,
                        align_x=0,
                        margin_y=0.2,
                        margin_x=0.5,
                        # TODO: Get rid of min_width
                        min_width=9.5,
                    ),
                    fill=self.session.theme.background_color,
                    stroke_color=self.styling_color,
                    hover_stroke_color=self.session.theme.primary_color,
                    stroke_width=0.1,
                    corner_radius=self.session.theme.corner_radius_small,
                ),
                on_press=self.on_press,
            ),
            content=PopupRectangle(
                self.options,
                self.selected_values,
                on_change_option=self.on_change_option,
            ),
            # Bind the is_open attribute so that the popup can be closed by the
            # user and preserve the correct state
            is_open=self.bind().is_open,
            position="bottom",
            user_closable=self.user_closable,
            alignment=self.alignment,
            gap=self.gap,
        )
