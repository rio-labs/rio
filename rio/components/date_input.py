from __future__ import annotations

import random
import typing as t
from dataclasses import KW_ONLY
from datetime import date

import rio

from .. import components as comps
from .component import Component

__all__ = [
    "DateInput",
]


def make_fake_input_box(
    *,
    theme: rio.Theme,
    label: str,
    value: str,
    style: t.Literal["underlined", "rounded", "pill"] = "underlined",
) -> rio.Component:
    """
    Creates something that looks like an input box, but is defined entirely
    Python-side. This is used as a sort of backdrop of the date input.
    """
    palette = theme.neutral_palette

    label_style = rio.TextStyle(
        fill=theme.secondary_color,
        font_size=0.8,
    )

    def define_content(
        corner_radius: float | t.Tuple[float, float, float, float],
    ) -> rio.Component:
        return rio.Rectangle(
            content=rio.Row(
                rio.Column(
                    rio.Text(
                        label,
                        selectable=False,
                        style=label_style,
                    ),
                    rio.Text(
                        value,
                        justify="left",
                        selectable=False,
                        margin_bottom=0.4,
                        align_y=1,
                        grow_x=True,
                    ),
                    # spacing=0.8,
                    grow_y=True,
                ),
                rio.Icon(
                    "material/calendar_today:fill",
                    fill="dim",
                    min_width=1.5,
                    min_height=1.5,
                    margin_bottom=0.3,
                    align_y=0.5,
                    align_x=1,
                ),
                spacing=0.8,
                margin_x=1,
                # make sure the value is centered if no label was added
                margin_top=0.3 if label == "" else 0.5,
            ),
            fill=palette.background,
            hover_fill=palette.background_active,
            corner_radius=corner_radius,
            cursor=rio.CursorStyle.POINTER,
            grow_y=True,
            transition_time=0.1,
        )

    if style == "underlined":
        corner_radius = (
            theme.corner_radius_small,
            theme.corner_radius_small,
            0,
            0,
        )
        return rio.Column(
            define_content(corner_radius),
            # Accent line at the bottom
            rio.Rectangle(
                fill=palette.foreground.replace(opacity=0.15),
                min_height=0.12,
            ),
            min_width=9,
        )
    elif style == "rounded":
        corner_radius = theme.corner_radius_small
        return define_content(corner_radius)

    elif style == "pill":
        corner_radius = 99999999

        return define_content(corner_radius)


@t.final
class DateInput(Component):
    """
    Allows the user to pick a date from a calendar.

    DateInputs are similar in appearance to `TextInput` and `NumberInput`, but
    allow the user to pick a date from a calendar, rather than text or number.
    When pressed, a calendar will pop-up, allowing the user to select a date.

    This makes for a compact component, which still allows the user to visually
    select a date.

    For a larger component which permanently displays a calendar, consider using
    `rio.Calendar`.


    ## Attributes

    `value`: The currently selected date.

    `label`: A short text to display next to the input field.

    `style`: Changes the visual appearance of the date input.

    `on_change`: Triggered whenever the user selects a new date.


    ## Examples

    Here's a simple example that allows the user to select a data and displays
    it back to them:

    ```python
    from datetime import date

    class MyComponent(rio.Component):
        value: date = date.today()

        def build(self) -> rio.Component:
            return rio.Column(
                rio.DateInput(
                    # In order to retrieve a value from the component, we'll
                    # use an attribute binding. This way our own value will
                    # be updated whenever the user changes the value.
                    value=self.bind().value,
                    label="Pick a Date",
                ),
                rio.Text(f"You've selected: {self.value}"),
            )
    ```

    Alternatively you can also attach an event handler to react to changes. This
    is a little more verbose, but allows you to run arbitrary code when the user
    picks a new date:

    ```python
    from datetime import date

    class MyComponent(rio.Component):
        value: date = date.today()

        def on_value_change(self, event: rio.DateChangeEvent):
            # This function will be called whenever the input's value
            # changes. We'll display the new value in addition to updating
            # our own attribute.
            self.value = event.value
            print(f"You've selected: {self.value}")

        def build(self) -> rio.Component:
            return rio.DateInput(
                value=self.value,
                label="Pick a Date",
                on_change=self.on_value_change,
            )
    ```


    ## Metadata

    `experimental`: True
    """

    value: date

    _: KW_ONLY

    label: str = ""
    style: t.Literal["underlined", "rounded", "pill"] = "underlined"
    on_change: rio.EventHandler[rio.DateChangeEvent] = None

    _is_open: bool = False

    async def _on_value_change(self, event: rio.DateChangeEvent) -> None:
        # Close the date picker
        self._is_open = False

        # Chain the event handler
        await self.call_event_handler(self.on_change, event)

    def _on_toggle_open(self, _: rio.PointerEvent) -> None:
        self._is_open = not self._is_open

    def _on_close(self) -> None:
        self._is_open = False

    def build(self) -> rio.Component:
        return rio.Popup(
            # Place a fake textbox. It's only used for styling and displaying
            # the label, if any
            anchor=rio.PointerEventListener(
                content=make_fake_input_box(
                    theme=self.session.theme,
                    label=self.label,
                    value=self.value.strftime(self.session._date_format_string),
                    style=self.style,
                ),
                on_press=self._on_toggle_open,
            ),
            # Display a calendar so the user can pick a date
            content=rio.Column(
                comps.Calendar(
                    value=self.bind().value,
                    on_change=self._on_value_change,
                    # Use a fresh calendar each time, so it displays the
                    # currently selected value each time the popup opens
                    key=str(random.random()),
                ),
                rio.Button(
                    "Cancel",
                    style="colored-text",
                    on_press=self._on_close,
                ),
                margin=1,
            ),
            color="neutral",
            position="center",
            alignment=0.5,
            is_open=self._is_open,
        )
