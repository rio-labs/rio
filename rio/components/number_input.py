from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings

import rio

from .keyboard_focusable_components import KeyboardFocusableComponent

__all__ = [
    "NumberInput",
    "NumberInputChangeEvent",
    "NumberInputConfirmEvent",
    "NumberInputFocusEvent",
]


# These must be ints so that `integer * multiplier` returns an int and not a
# float
_multiplier_suffixes: t.Mapping[str, int] = {
    "k": 1_000,
    "m": 1_000_000,
}


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
class NumberInput(KeyboardFocusableComponent):
    """
    Like `TextInput`, but specifically for inputting numbers.

    `NumberInput` allows the user to enter a number. This is similar to the
    `TextInput` component, but with some goodies specifically for handling
    numbers. The value is automatically parsed and formatted according to the
    user's locale, and you can specify minimum and maximum values to limit the
    user's input.

    Number inputs go way beyond just parsing the input using `int` or `float`.
    They try their best to understand what the user is trying to enter, and also
    support suffixes such as "k" and "m" to represent thousands and millions
    respectively.


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

    `thousands_separator`: By default, the number is formatted according to the
        user's locale. This means numbers will show up correctly for everyone,
        regardless of where they live and which thousands separator they use.
        If you want to override this behavior, you can set this attribute to
        `False`. This will disable the thousands separator altogether.
        Alternatively, provide a custom string to use as the thousands
        separator.

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
    thousands_separator: bool | str = True
    is_sensitive: bool = True
    is_valid: bool = True

    on_change: rio.EventHandler[NumberInputChangeEvent] = None
    on_confirm: rio.EventHandler[NumberInputConfirmEvent] = None

    on_gain_focus: rio.EventHandler[NumberInputFocusEvent] = None
    on_lose_focus: rio.EventHandler[NumberInputFocusEvent] = None

    def __post_init__(self):
        self._text_input: rio.TextInput | None = None

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

    async def _on_gain_focus(self, ev: rio.TextInputFocusEvent) -> None:
        await self.call_event_handler(
            self.on_gain_focus,
            NumberInputFocusEvent(self.value),
        )

    async def _on_lose_focus(self, ev: rio.TextInputFocusEvent) -> None:
        was_updated = self._try_set_value(ev.text)

        if was_updated:
            await self.call_event_handler(
                self.on_change,
                NumberInputChangeEvent(self.value),
            )

        await self.call_event_handler(
            self.on_lose_focus,
            NumberInputFocusEvent(self.value),
        )

    async def _on_confirm(self, ev: rio.TextInputConfirmEvent) -> None:
        was_updated = self._try_set_value(ev.text)

        if was_updated:
            await self.call_event_handler(
                self.on_change,
                NumberInputChangeEvent(self.value),
            )

            await self.call_event_handler(
                self.on_confirm,
                NumberInputConfirmEvent(self.value),
            )

    def _formatted_value(self) -> str:
        """
        Convert the given number to a string, formatted according to the
        component's settings.
        """
        # Otherwise use the locale's settings
        if self.decimals == 0:
            int_str, frac_str = f"{self.value:.0f}", ""
        else:
            int_str, frac_str = f"{self.value:.{self.decimals}f}".split(".")

        # Add the thousands separators
        if self.thousands_separator is True:
            thousands_separator = self._session_._thousands_separator
        elif self.thousands_separator is False:
            thousands_separator = ""
        else:
            thousands_separator = self.thousands_separator

        integer_part_with_sep = f"{int(int_str):,}".replace(
            ",", thousands_separator
        )

        # Construct the final formatted number
        if self.decimals == 0:
            return integer_part_with_sep

        return f"{integer_part_with_sep}{self.session._decimal_separator}{frac_str}"

    def build(self) -> rio.Component:
        text_input = rio.TextInput(
            text=self._formatted_value(),
            label=self.label,
            style=self.style,
            prefix_text=self.prefix_text,
            suffix_text=self.suffix_text,
            is_sensitive=self.is_sensitive,
            is_valid=self.is_valid,
            accessibility_label=self.accessibility_label,
            auto_focus=self.auto_focus,
            on_confirm=self._on_confirm,
            on_gain_focus=self._on_gain_focus,
            on_lose_focus=self._on_lose_focus,
        )

        if self._text_input is None:
            self._text_input = text_input

        return text_input

    async def grab_keyboard_focus(self) -> None:
        if self._text_input is not None:
            await self._text_input.grab_keyboard_focus()
