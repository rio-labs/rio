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

    It's similar to `TextInput`, but it allows the user to enter multiple lines of text.

    `MultiLineTextInput` allows the user to enter a short text. The text can either be
    shown in plain text or other sensitive information.


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

    A minimal example of `MultiLineTextInput` with a default text of "" will be shown:
    `Note`: The text will not be updated if the user changes the text in the input field.

    ```python
    rio.MultiLineTextInput(text="")
    ```

    You can easily bind state variables to track changes. If you want to make your
    `MultiLineTextInput` more responsive, you can easily achieve this by adding a
    lambda function call to e.g. on_change:

    ```python
    class MyComponent(rio.Component):
        text: str = ""

        def build(self) -> rio.Component:
            return rio.MultiLineTextInput(
                text=self.bind().text,  # attribute binding
                label="Write your comments here",
                on_change=lambda event: print(event.text),
            )
    ```

    You can also use a method for updating the input text and do whatever you want.
    Note that methods are handy if you want to do more than just updating the input
    text. For example run async code or update other components based on the input text:

    ```python
    class MyComponent(rio.Component):
        text: str = ""

        def on_change_update_text(self, event: rio.MultiLineTextInputChangeEvent):
            self.text = event.text
            # You can do whatever you want in here

        def build(self) -> rio.Component:
            return rio.MultiLineTextInput(
                text=self.text,
                label="Write your comments here",
                on_change=self.on_change_update_text,
            )
    ```
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
