from __future__ import annotations

# <additional-imports>
import functools
import typing as t

import rio

from .. import components as comps

# </additional-imports>

# <component>
T = t.TypeVar("T")


class DropdownElement(rio.Component):
    """
    A custom component to display a rectangle with text and an icon.

    The option can be selected and deselected.


    ## Attributes:

    `name`: The name of the option.

    `is_selected`: A boolean indicating whether the option is selected.

    `on_press`: An event handler triggered when the option is pressed.
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
    """
    A popup rectangle component used to display a dropdown or popup menu.


    ## Attributes:

    `options`: A mapping of string keys to selectable values.

    `selected_values`: A list of currently selected values.

    `on_change_option`: An event handler triggered when an option is selected.

    """

    options: t.Mapping[str, T]
    selected_values: list[T]

    on_change_option: rio.EventHandler[[str]] = None

    async def _on_change_option(self, option: str) -> None:
        await self.call_event_handler(self.on_change_option, option)
        self.force_refresh()

    def build(self) -> rio.Component:
        content = rio.Column(margin=0.5, spacing=0.5)

        # Populate dropdown content
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


class MultiSelectDropdown(rio.Component, t.Generic[T]):
    """
    A customizable multi-select dropdown component that maps string keys to
    generic values.


    ## Attributes:

    `label`: The label displayed for the dropdown.

    `label_icon`: The icon displayed next to the label.

    `options`: A mapping of string keys to selectable values.

    `selected_values`: A list of currently selected values.

    `styling_color`: The color used for styling the dropdown.

    `on_change`: An event handler triggered when the selected values change.
    """

    label: str
    label_icon: str
    options: t.Mapping[str, T]
    selected_values: list[T] = []
    styling_color: rio.Color = rio.Color.GRAY
    on_change: rio.EventHandler[comps.MultiSelectDropdownChangeEvent[T]] = None

    _is_open: bool = False

    async def on_change_option(self, option_key: str) -> None:
        """
        Toggle the selection of the option.
        """
        # Handle Mapping[str, T]
        option_value = self.options[option_key]

        # Update the selected values based on the option's current selection
        # state
        if option_value in self.selected_values:
            self.selected_values.remove(option_value)
        else:
            self.selected_values.append(option_value)

        # Copy list
        values = self.selected_values

        await self.call_event_handler(
            self.on_change,
            comps.MultiSelectDropdownChangeEvent(values.copy()),
        )

        # Rio automatically detects assignments to the components attributes.
        # However, since we've modified the attributes in-place without any
        # assignments we have to manually force a refresh.
        self.force_refresh()

    def on_press(self, _: rio.PointerEvent) -> None:
        """
        Toggle the dropdown open state
        """
        self._is_open = not self._is_open

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
                options=self.options,
                selected_values=self.selected_values,
                on_change_option=self.on_change_option,
            ),
            # Bind the is_open attribute so that the popup can be closed by the
            # user and preserve the correct state
            is_open=self.bind()._is_open,
            position="bottom",
            user_closable=True,
        )


# </component>
