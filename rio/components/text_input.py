from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .keyboard_focusable_components import KeyboardFocusableFundamentalComponent

__all__ = [
    "TextInput",
    "TextInputChangeEvent",
    "TextInputConfirmEvent",
    "TextInputFocusEvent",
]


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class TextInputChangeEvent:
    """
    Holds information regarding a text input change event.

    This is a simple dataclass that stores useful information for when the user
    changes the text in a `TextInput`. You'll typically receive this as argument
    in `on_change` events.

    ## Attributes

    `text`: The new `text` of the `TextInput`.
    """

    text: str


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class TextInputConfirmEvent:
    """
    Holds information regarding a text input confirm event.

    This is a simple dataclass that stores useful information for when the user
    confirms the text in a `TextInput`. You'll typically receive this as
    argument in `on_confirm` events.

    ## Attributes

    `text`: The new `text` of the `TextInput`.
    """

    text: str


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class TextInputFocusEvent:
    """
    Holds information regarding a text input focus event.

    This is a simple dataclass that stores useful information for when a
    `TextInput` gains or loses focus. You'll typically receive this as argument
    in `on_gain_focus` and `on_lose_focus` events.

    ## Attributes

    `text`: The `text` of the `TextInput`.
    """

    text: str


@t.final
class TextInput(KeyboardFocusableFundamentalComponent):
    """
    A user-editable text field.

    `TextInput` allows the user to enter a short text. The text can either be
    shown in plain text, or hidden when used for passwords or other sensitive
    information.


    ## Attributes

    `text`: The text currently entered by the user.

    `label`: A short text to display next to the text input.

    `accessibility_label`: A short text describing the text input for screen
        readers. If omitted, the `label` text is used.

    `style`: Changes the visual appearance of the text input.

    `prefix_text`: A short text to display before the text input. Useful for
            displaying currency symbols or other prefixed units.

    `suffix_text`: A short text to display after the text input. Useful for
            displaying units, parts of e-mail addresses, and similar.

    `is_secret`: Whether the text should be hidden. Use this to hide sensitive
            information such as passwords.

    `is_sensitive`: Whether the text input should respond to user input.

    `is_valid`: Visually displays to the user whether the current text is
            valid. You can use this to signal to the user that their input needs
            to be changed.

    `on_change`: Triggered when the user changes the text.

    `on_confirm`: Triggered when the user explicitly confirms their input,
            such as by pressing the "Enter" key. You can use this to trigger
            followup actions, such as logging in or submitting a form.

    `on_gain_focus`: Triggered when the user selects the number input, i.e. it
        gains focus.

    `on_lose_focus`: Triggered when the user switches from the `NumberInput` to
        another component, i.e. it loses focus.


    ## Examples

    Here's a simple example that allows the user to enter a value and displays
    it back to them:

    ```python
    class MyComponent(rio.Component):
        text: str = "Hello, World!"

        def build(self) -> rio.Component:
            return rio.Column(
                rio.TextInput(
                    # In order to retrieve a value from the component, we'll
                    # use an attribute binding. This way our own value will
                    # be updated whenever the user changes the text.
                    text=self.bind().text,
                    label="Enter a Text",
                ),
                rio.Text(f"You've typed: {self.text}"),
            )
    ```

    Alternatively you can also attach an event handler to react to changes. This
    is a little more verbose, but allows you to run arbitrary code when the user
    changes the text:

    ```python
    class MyComponent(rio.Component):
        text: str = "Hello, World!"

        def on_value_change(self, event: rio.TextInputChangeEvent):
            # This function will be called whenever the input's value
            # changes. We'll display the new value in addition to updating
            # our own attribute.
            self.text = event.text
            print(f"You've typed: {self.text}")

        def build(self) -> rio.Component:
            return rio.TextInput(
                text=self.text,
                label="Enter a Text",
                on_change=self.on_value_change,
            )
    ```
    """

    text: str = ""
    _: dataclasses.KW_ONLY
    label: str = ""
    accessibility_label: str = ""
    style: t.Literal["underlined", "rounded", "pill"] = "underlined"
    prefix_text: str = ""
    suffix_text: str = ""
    is_secret: bool = False
    is_sensitive: bool = True
    is_valid: bool = True

    on_change: rio.EventHandler[TextInputChangeEvent] = None
    on_confirm: rio.EventHandler[TextInputConfirmEvent] = None

    on_gain_focus: rio.EventHandler[TextInputFocusEvent] = None
    on_lose_focus: rio.EventHandler[TextInputFocusEvent] = None

    def _custom_serialize_(self) -> JsonDoc:
        # The other events have the secondary effect of updating the TextInput's
        # value, so `on_gain_focus` is the only one that can be omitted
        return {
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
            old_value = self.text

            new_value = msg["text"]
            assert isinstance(new_value, str)

            self._apply_delta_state_from_frontend({"text": new_value})

            value_has_changed = old_value != new_value
        else:
            new_value = self.text
            value_has_changed = False

        # What sort of event is this?
        event_type = msg.get("type")

        # Gain focus
        if event_type == "gainFocus":
            await self.call_event_handler(
                self.on_gain_focus,
                TextInputFocusEvent(new_value),
            )

        # Lose focus
        elif event_type == "loseFocus":
            if value_has_changed:
                await self.call_event_handler(
                    self.on_change,
                    TextInputChangeEvent(new_value),
                )

            await self.call_event_handler(
                self.on_lose_focus,
                TextInputFocusEvent(new_value),
            )

        # Change
        elif event_type == "change":
            if self.is_sensitive and value_has_changed:
                await self.call_event_handler(
                    self.on_change,
                    TextInputChangeEvent(new_value),
                )

        # Confirm
        elif event_type == "confirm":
            if self.is_sensitive:
                if value_has_changed:
                    await self.call_event_handler(
                        self.on_change,
                        TextInputChangeEvent(new_value),
                    )

                await self.call_event_handler(
                    self.on_confirm,
                    TextInputConfirmEvent(new_value),
                )

        # Invalid
        else:
            raise AssertionError(
                f"Received invalid event from the frontend: {msg}"
            )


TextInput._unique_id_ = "TextInput-builtin"
