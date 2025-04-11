from __future__ import annotations

# <additional-imports>
import dataclasses
import functools
import typing as t

import rio

# </additional-imports>

# <component>
T = t.TypeVar("T")


@dataclasses.dataclass
class SingleSelectDropdownChangeEvent(t.Generic[T]):
    """
    Holds information regarding a dropdown change event.

    This is a simple dataclass that stores useful information for when the user
    selects an option in a `Dropdown`. You'll typically receive this as argument
    in `on_change` events.

    ## Attributes

    `value`: The new `selected_value` of the `Dropdown`.
    """

    value: T


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
    options: t.Mapping[str, T] | t.Sequence[T]
    selected_value: T

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
                        is_selected=option_value == self.selected_value,
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
                        is_selected=option_value == self.selected_value,
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


class SingleSelectDropdownStyledHeader(rio.Component, t.Generic[T]):
    text: str
    icon: str
    options: t.Mapping[str, T] | t.Sequence[T]
    selected_value: T | None = None
    styling_color: rio.Color = rio.Color.GRAY
    user_closable: bool = True
    alignment: float = 0.5
    gap: float = 0.8

    is_open: bool = False

    on_change: rio.EventHandler[SingleSelectDropdownChangeEvent[T]] = None

    def __post_init__(self) -> None:
        """
        Automatically set the selected_value to the first entry of options
        if it is not explicitly specified.
        """
        if self.selected_value is None:
            if isinstance(self.options, t.Mapping):
                # Get the first value from the mapping
                self.selected_value = next(iter(self.options.values()), None)
            elif isinstance(self.options, t.Sequence) and len(self.options) > 0:
                # Get the first value from the sequence
                self.selected_value = self.options[0]

    def on_change_option(self, option_key_or_value: str | T | None) -> None:
        """
        Set the selected option. Handles both Mapping and Sequence cases.
        """
        # Handle Mapping[str, T]
        if isinstance(self.options, t.Mapping):
            if not isinstance(option_key_or_value, str):
                raise TypeError("Expected a string key for Mapping options.")
            option_value = self.options[option_key_or_value]

        # Handle Sequence[T]
        elif isinstance(self.options, t.Sequence):
            if not isinstance(
                option_key_or_value, type(next(iter(self.options), None))
            ):
                raise TypeError(
                    "Expected a value of type T for Sequence options."
                )
            option_value = option_key_or_value

        # Raise an error if the options are not a Mapping or Sequence
        else:
            raise TypeError("Unsupported type for options.")

        # Update the selected value
        self.selected_value = option_value
        self.is_open = False
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
                            self.icon,
                            fill=self.styling_color,
                            align_y=0.5,
                            min_width=1.2,
                            min_height=1.2,
                        ),
                        rio.Text(
                            self.text,
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
                self.selected_value,
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


# </component>
