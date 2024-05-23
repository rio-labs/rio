from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any, final

from uniserde import JsonDoc

import rio

from .fundamental_component import KeyboardFocusableFundamentalComponent

__all__ = [
    "MultiLineTextInput",
    "MultiLineTextInputChangeEvent",
    "MultiLineTextInputConfirmEvent",
]


@final
@dataclass
class MultiLineTextInputChangeEvent:
    text: str


@final
@dataclass
class MultiLineTextInputConfirmEvent:
    text: str


@final
class MultiLineTextInput(KeyboardFocusableFundamentalComponent):
    """
    A user-editable text field.

    `MultiLineTextInput` is a text input field similar to the regular
    `TextInput`, but allows the user to enter multiple lines of text.

    ## Attributes

    `text`: The text currently entered by the user.

    `label`: A short text to display next to the text input.

    `is_sensitive`: Whether the text input should respond to user input.

    `is_valid`: Visually displays to the user whether the current text is
        valid. You can use this to signal to the user that their input needs
        to be changed.

    `on_change`: Triggered when the user changes the text.

    `on_confirm`: Triggered when the user explicitly confirms their input,
        such as by pressing the "Enter" key. You can use this to trigger
        followup actions, such as logging in or submitting a form.


    ## Examples

    Here's a simple example that allows the user to enter a value and displays
    it back to them:

    ```python
    class MyComponent(rio.Component):
        text: str = "Hello, World!"

        def build(self) -> rio.Component:
            return rio.Column(
                rio.MultiLineTextInput(
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

        def on_value_change(self, event: rio.MultiLineTextInputChangeEvent):
            # This function will be called whenever the input's value
            # changes. We'll display the new value in addition to updating
            # our own attribute.
            self.text = event.text
            print(f"You've typed: {self.text}")

        def build(self) -> rio.Component:
            return rio.MultiLineTextInput(
                text=self.text,
                label="Enter a Text",
                on_change=self.on_value_change,
            )
    ```


    ## Metadata

    experimental: True
    """

    text: str = ""
    _: KW_ONLY
    label: str = ""
    is_sensitive: bool = True
    is_valid: bool = True
    on_change: rio.EventHandler[MultiLineTextInputChangeEvent] = None
    on_confirm: rio.EventHandler[MultiLineTextInputConfirmEvent] = None

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"text"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

        if "text" in delta_state and not self.is_sensitive:
            raise AssertionError(
                f"Frontend tried to set `MultiLineTextInput.text` even though `is_sensitive` is `False`"
            )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        # Trigger on_change event
        try:
            new_value = delta_state["text"]
        except KeyError:
            pass
        else:
            assert isinstance(new_value, str), new_value
            await self.call_event_handler(
                self.on_change,
                MultiLineTextInputChangeEvent(new_value),
            )

        self._apply_delta_state_from_frontend(delta_state)

    async def _on_message(self, msg: Any) -> None:
        # Listen for messages indicating the user has confirmed their input
        #
        # In addition to notifying the backend, these also include the input's
        # current value. This ensures any event handlers actually use the up-to
        # date value.
        assert isinstance(msg, dict), msg

        self._apply_delta_state_from_frontend({"text": msg["text"]})

        await self.call_event_handler(
            self.on_change,
            MultiLineTextInputChangeEvent(self.text),
        )

        await self.call_event_handler(
            self.on_confirm,
            MultiLineTextInputConfirmEvent(self.text),
        )

        # Refresh the session
        await self.session._refresh()


MultiLineTextInput._unique_id = "MultiLineTextInput-builtin"
