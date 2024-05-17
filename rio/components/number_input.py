from __future__ import annotations

from collections.abc import Mapping
from dataclasses import KW_ONLY, dataclass
from typing import *  # type: ignore

import rio.docs

from .component import Component

__all__ = [
    "NumberInput",
    "NumberInputChangeEvent",
    "NumberInputConfirmEvent",
]


# These must be ints so that `integer * multiplier` returns an int and not a
# float
_multiplier_suffixes: Mapping[str, int] = {
    "k": 1_000,
    "m": 1_000_000,
}


@final
@rio.docs.mark_constructor_as_private
@dataclass
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


@final
@rio.docs.mark_constructor_as_private
@dataclass
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


@final
class NumberInput(Component):
    """
    Like `TextInput`, but specifically for inputting numbers.

    `NumberInput` allows the user to enter a number. This is similar to the
    `TextInput` component, but with some goodies for handling numbers. The value
    is automatically parsed and formatted according to the user's locale, and
    you can specify minimum and maximum values to limit the user's input.

    Number inputs go way beyond just parsing the input using `int` or `float`.
    They try their best to understand what the user is trying to enter, and also
    support suffixes such as "k" and "m" to represent thousands and millions
    respectively.


    ## Attributes

    `value`: The number currently entered by the user.

    `label`: A short text to display next to the text input.

    `prefix_text`: A short text to display before the text input. Useful for
        displaying currency symbols or other prefixed units.

    `suffix_text`: A short text to display after the text input. Useful for
        displaying currency names or units.

    `minimum`: The minimum value the number can be set to.

    `maximum`: The maximum value the number can be set to.

    `decimals`: The number of decimals to accept. If the user enters more
        decimals, they will be rounded off. If this value is equal to `0`, the
        input's `value` is guaranteed to be an integer, rather than float.

    `is_sensitive`: Whether the text input should respond to user input.

    `is_valid`: Visually displays to the user whether the current text is
        valid. You can use this to signal to the user that their input needs to
        be changed.

    `on_change`: Triggered when the user changes the number.

    `on_confirm`: Triggered when the user explicitly confirms their input,
        such as by pressing the "Enter" key.


    ## Examples

    A minimal example of `NumberInput` with a default value of 20.00 will be
    shown: Note: The text will not be updated if the user changes the value in
    the input field.

    ```python
    rio.NumberInput(value=20.00)
    ```

    You can easily bind state variables to track changes. If you want to make
    your `NumberInput` more responsive, you can easily achieve this by adding a
    lambda function call to e.g. on_change:

    ```python
    class MyComponent(rio.Component):
        value: float = 0.0

        def build(self) -> rio.Component:
            return rio.NumberInput(
                value=self.bind().value,  # attribute binding
                label="price",
                prefix_text="$",
                minimum=0,
                decimals=2,
                on_change=lambda event: print(f"value: {event.value}"),
            )
    ```

    You can also use a method for updating the input value and do whatever you
    want. Note that methods are handy if you want to do more than just updating
    the input value. For example run async code or update other components based
    on the input text:

    ```python
    class MyComponent(rio.Component):
        value: float = 0.0

        def on_change_update_value(self, event: rio.NumberInputChangeEvent):
            self.value = event.value
            print(f"new value: {self.value}")
            # You can do whatever you want with the new value

        def build(self) -> rio.Component:
            return rio.NumberInput(
                value=self.value,
                label="price",
                prefix_text="$",
                minimum=0,
                decimals=2,
                on_change=self.on_change_update_value,
            )
    ```
    """

    value: float = 0
    _: KW_ONLY
    label: str = ""
    prefix_text: str = ""
    suffix_text: str = ""
    minimum: float | None = None
    maximum: float | None = None
    decimals: int = 2
    is_sensitive: bool = True
    is_valid: bool = True
    on_change: rio.EventHandler[NumberInputChangeEvent] = None
    on_confirm: rio.EventHandler[NumberInputConfirmEvent] = None

    def __post_init__(self):
        self._text_input = None

    def _try_set_value(self, raw_value: str) -> bool:
        """
        Parse the given string and update the component's value accordingly.
        Returns `True` if the value was successfully updated, `False` otherwise.
        """

        # Strip the number down as much as possible
        raw_value = raw_value.strip()
        raw_value = raw_value.replace(self.session._thousands_separator, "")

        # If left empty, set the value to 0, if that's allowable
        if not raw_value:
            self.value = 0

            if self.minimum is not None and self.minimum > 0:
                self.value = self.minimum

            if self.maximum is not None and self.maximum < 0:
                self.value = self.maximum

            return True

        # Check for a multiplier suffix
        suffix = raw_value[-1].lower()
        multiplier = 1

        if suffix.isalpha():
            try:
                multiplier = _multiplier_suffixes[suffix]
            except KeyError:
                pass
            else:
                raw_value = raw_value[:-1].rstrip()

        # Try to parse the number
        try:
            value = float(
                raw_value.replace(self.session._decimal_separator, ".")
            )
        except ValueError:
            self.value = self.value  # Force the old value to stay
            return False

        # Apply the multiplier
        value *= multiplier

        # Limit the number of decimals
        #
        # Ensure the value is an integer, if the number of decimals is 0
        value = round(value, None if self.decimals == 0 else self.decimals)

        # Clamp the value
        minimum = self.minimum
        if minimum is not None:
            value = max(value, minimum)

        maximum = self.maximum
        if maximum is not None:
            value = min(value, maximum)

        # Update the value
        self.value = value
        return True

    async def _on_change(self, ev: rio.TextInputChangeEvent) -> None:
        was_updated = self._try_set_value(ev.text)

        if was_updated:
            await self.call_event_handler(
                self.on_change,
                NumberInputChangeEvent(self.value),
            )

    async def _on_confirm(self, ev: rio.TextInputConfirmEvent) -> None:
        was_updated = self._try_set_value(ev.text)

        if was_updated:
            await self.call_event_handler(
                self.on_confirm,
                NumberInputConfirmEvent(self.value),
            )

    def build(self) -> rio.Component:
        # Format the number
        value_str = f"{self.value:.{self.decimals}f}"
        if self.decimals == 0:
            int_str, frac_str = value_str, ""
        else:
            int_str, frac_str = value_str.split(".")

        # Add thousands separators
        groups = []
        group_limit = 4 if int_str[0] == "-" else 3  # 4 so `-` is not counted

        while len(int_str) > group_limit:
            groups.append(int_str[-3:])
            int_str = int_str[:-3]

        groups.append(int_str)
        int_str = self.session._thousands_separator.join(reversed(groups))

        # Join the strings
        if self.decimals == 0:
            value_str = int_str
        else:
            value_str = int_str + self.session._decimal_separator + frac_str

        # Build the component
        self._text_input = rio.TextInput(
            text=value_str,
            label=self.label,
            prefix_text=self.prefix_text,
            suffix_text=self.suffix_text,
            is_sensitive=self.is_sensitive,
            is_valid=self.is_valid,
            on_change=self._on_change,
            on_confirm=self._on_confirm,
        )
        return self._text_input

    async def grab_keyboard_focus(self) -> None:
        """
        ## Metadata

        public: False
        """
        if self._text_input is not None:
            await self._text_input.grab_keyboard_focus()
