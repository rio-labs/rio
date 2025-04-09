from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .keyboard_focusable_components import KeyboardFocusableFundamentalComponent

__all__ = [
    "NumberInput",
    "NumberInputChangeEvent",
    "NumberInputConfirmEvent",
    "NumberInputFocusEvent",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class NumberInputChangeEvent:
    """
    Holds information regarding a number change event.

    This is a simple dataclass that stores useful information for when the user
    changes a number. You'll typically receive this as argument in `on_change`
    events.

    ## Attributes

    `value`: The new `value` of the `NumberInput`.
    """

    value: float


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class NumberInputConfirmEvent:
    """
    Holds information regarding a number confirm event.

    This is a simple dataclass that stores useful information for when the user
    confirms a number. You'll typically receive this as argument in `on_confirm`
    events.

    ## Attributes

    `value`: The new `value` of the `NumberInput`.
    """

    value: float


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class NumberInputFocusEvent:
    """
    Holds information regarding a number input focus event.

    This is a simple dataclass that stores useful information for when a
    `NumberInput` gains or loses focus. You'll typically receive this as
    argument in `on_gain_focus` and `on_lose_focus` events.

    ## Attributes

    value: The `value` of the `NumberInput`.
    """

    value: float


@t.final
class NumberInput(KeyboardFocusableFundamentalComponent):
    """
    Like `NumberInput`, but specifically for inputting numbers.

    `NumberInput` allows the user to enter a number. This is similar to the
    `NumberInput` component, but with some goodies specifically for handling
    numbers. The value is automatically parsed and formatted according to the
    user's locale, and you can specify minimum and maximum values to limit the
    user's input.

    Number inputs go way beyond just parsing the input using `int` or `float`.
    They support suffixes such as "k" and "m" to represent thousands and
    millions respectively, and even mathematical expressions such as `2 + 3` or
    `2 * (3 + 1)`.


    ## Attributes

    `value`: The number currently entered by the user.

    `label`: A short text to display next to the number input.

    `accessibility_label`: A short text describing the text input for screen
        readers. If omitted, the `label` text is used.

    `style`: Changes the visual appearance of the text input.

    `prefix_text`: A short text to display before the number input. Useful for
        displaying currency symbols or other prefixed units.

    `suffix_text`: A short text to display after the number input. Useful for
        displaying currency names or units.

    `minimum`: The minimum value the number can be set to.

    `maximum`: The maximum value the number can be set to.

    `decimals`: The number of decimals to accept. If the user enters more
        decimals, they will be rounded off. If this value is equal to `0`, the
        input's `value` is guaranteed to be an integer, rather than float.

    `decimal_separator`: By default, the number is formatted according to the
        user's locale. This means numbers will show up correctly for everyone,
        regardless of where they live and which thousands separator they use. If
        you want to override this behavior, you can use this attribute to set a
        decimal separator of your choice.

    `thousands_separator`: By default, the number is formatted according to the
        user's locale. This means numbers will show up correctly for everyone,
        regardless of where they live and which thousands separator they use. If
        you want to override this behavior, you can use this attribute to set a
        thousands separator of your choice.

    `is_sensitive`: Whether the text input should respond to user input.

    `is_valid`: Visually displays to the user whether the current text is
        valid. You can use this to signal to the user that their input needs to
        be changed.

    `on_change`: Triggered when the user changes the number.

    `on_confirm`: Triggered when the user explicitly confirms their input,
        such as by pressing the "Enter" key.

    `on_gain_focus`: Triggered when the user selects the number input, i.e. it
        gains focus.

    `on_lose_focus`: Triggered when the user switches from the `NumberInput` to
        another component, i.e. it loses focus.

    ## Examples

    Here's a simple example that allows the user to select a value and displays
    it back to them:

    ```python
    class MyComponent(rio.Component):
        value: float = 1

        def build(self) -> rio.Component:
            return rio.Column(
                rio.NumberInput(
                    # In order to retrieve a value from the component, we'll
                    # use an attribute binding. This way our own value will
                    # be updated whenever the user changes the text.
                    value=self.bind().value,
                    minimum=1,
                    maximum=10,
                ),
                rio.Text(f"You've selected: {self.value}"),
            )
    ```

    Alternatively you can also attach an event handler to react to changes. This
    is a little more verbose, but allows you to run arbitrary code when the user
    changes the text:

    ```python
    class MyComponent(rio.Component):
        value: float = 1

        def on_value_change(self, event: rio.NumberInputChangeEvent):
            # This function will be called whenever the input's value
            # changes. We'll display the new value in addition to updating
            # our own attribute.
            self.value = event.value
            print(f"You've selected: {self.value}")

        def build(self) -> rio.Component:
            return rio.NumberInput(
                value=self.value,
                minimum=1,
                maximum=10,
                on_change=self.on_value_change,
            )
    ```
    """

    value: float = 0
    _: dataclasses.KW_ONLY
    label: str = ""
    accessibility_label: str = ""
    style: t.Literal["underlined", "rounded", "pill"] = "underlined"
    prefix_text: str = ""
    suffix_text: str = ""
    minimum: float | None = None
    maximum: float | None = None
    decimals: int = 2
    decimal_separator: str | None = None
    thousands_separator: bool | str = True
    is_sensitive: bool = True
    is_valid: bool = True

    on_change: rio.EventHandler[NumberInputChangeEvent] = None
    on_confirm: rio.EventHandler[NumberInputConfirmEvent] = None

    on_gain_focus: rio.EventHandler[NumberInputFocusEvent] = None
    on_lose_focus: rio.EventHandler[NumberInputFocusEvent] = None

    def _custom_serialize_(self) -> JsonDoc:
        decimal_separator = self.decimal_separator
        if decimal_separator is None:
            decimal_separator = self._session_._decimal_separator

        thousands_separator = self.thousands_separator

        if thousands_separator is True:
            thousands_separator = self._session_._thousands_separator
        elif thousands_separator is False:
            thousands_separator = ""

        return {
            "decimal_separator": decimal_separator,
            "thousands_separator": thousands_separator,
            # The other events have the secondary effect of updating the
            # NumberInput's value, so `on_gain_focus` is the only one that can
            # be omitted
            "reportFocusGain": self.on_gain_focus is not None,
        }

    async def _on_message_(self, msg: t.Any) -> None:
        # Listen for messages indicating the user has confirmed their input
        #
        # In addition to notifying the backend, these also include the input's
        # current value. This ensures any event handlers actually use the
        # up-to-date value.
        assert isinstance(msg, dict), msg

        # Update the local state

        if self.is_sensitive:
            old_value = self.value

            new_value = msg["value"]
            assert isinstance(new_value, (int, float))

            self._apply_delta_state_from_frontend({"value": new_value})

            value_has_changed = old_value != self.value
        else:
            new_value = self.value
            value_has_changed = False

        # What sort of event is this?
        event_type = msg.get("type")

        # Gain focus
        if event_type == "gainFocus":
            await self.call_event_handler(
                self.on_gain_focus,
                NumberInputFocusEvent(new_value),
            )

        # Lose focus
        elif event_type == "loseFocus":
            if self.is_sensitive and value_has_changed:
                await self.call_event_handler(
                    self.on_change,
                    NumberInputChangeEvent(new_value),
                )

            await self.call_event_handler(
                self.on_lose_focus,
                NumberInputFocusEvent(new_value),
            )

        # Change
        elif event_type == "change":
            if self.is_sensitive and value_has_changed:
                await self.call_event_handler(
                    self.on_change,
                    NumberInputChangeEvent(new_value),
                )

        # Confirm
        elif event_type == "confirm":
            if self.is_sensitive:
                if value_has_changed:
                    await self.call_event_handler(
                        self.on_change,
                        NumberInputChangeEvent(new_value),
                    )

                await self.call_event_handler(
                    self.on_confirm,
                    NumberInputConfirmEvent(new_value),
                )

        # Invalid
        else:
            raise AssertionError(
                f"Received invalid event from the frontend: {msg}"
            )


NumberInput._unique_id_ = "NumberInput-builtin"
