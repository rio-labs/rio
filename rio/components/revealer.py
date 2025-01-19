from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "Revealer",
    "RevealerChangeEvent",
]

T = t.TypeVar("T")


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class RevealerChangeEvent:
    """
    Holds information regarding a revealer change event.

    This is a simple dataclass that stores useful information for when the user
    opens or closes a revealer. You'll typically receive this as argument in
    `on_change` events.

    ## Attributes

    `is_open`: The new `is_open` state of the `Revealer`.
    """

    is_open: bool


@t.final
class Revealer(FundamentalComponent):
    """
    A component that can be used to hide and reveal content.

    The `Revealer` is a versatile component that can be used to hide and reveal
    content. It can be used to create collapsible sections, or to hide and
    reveal content based on user input.

    If you specify a `header`, the revealer will automatically display a
    pressable header. Pressing the header will toggle the visibility of its
    content. If you don't specify a header, the revealer will only display its
    content, and must be expanded and collapsed programmatically.


    ## Attributes

    `header`: The header of the `Revealer`. If `None`, the `Revealer` will be
        hidden by default.

    `content`: The content to display when the `Revealer` is open.

    `header_style`: The style of the header. Can be one of `"heading1"`,
        `"heading2"`, `"heading3"`, or `"text"`.

    `is_open`: Whether the `Revealer` is open or not.

    `on_change`: An event handler that is called when the `Revealer` is opened
        or closed. The event handler receives a `RevealerChangeEvent` as input.


    ## Examples

    A simple `Revealer` that displays "Hello" when opened:

    ```python
    rio.Revealer(
        header="Click to reveal",
        content=rio.Text("Hello"),
    )
    ```

    A `Revealer` is a component that hides content, in this case a TextInput,
    until it's opened:

    ```python
    class MyComponent(rio.Component):
        def build(self) -> rio.Component:
            return rio.Revealer(
                header="Click to Reveal",
                content=rio.TextInput(
                    text="Hey there!",
                ),
                header_style="heading2",
            )
    ```
    """

    header: str | None
    content: rio.Component
    _: dataclasses.KW_ONLY
    header_style: (
        t.Literal["heading1", "heading2", "heading3", "text"] | rio.TextStyle
    ) = "text"
    is_open: bool = False
    on_change: rio.EventHandler[RevealerChangeEvent] = None

    def _validate_delta_state_from_frontend(self, delta_state: JsonDoc) -> None:
        if not set(delta_state) <= {"is_open"}:
            raise AssertionError(
                f"Frontend tried to change `{type(self).__name__}` state: {delta_state}"
            )

        if "is_open" in delta_state and self.header is None:
            raise AssertionError(
                f"Frontend tried to set `Revealer.is_open` even though it has no `header`"
            )

    async def _call_event_handlers_for_delta_state(
        self, delta_state: JsonDoc
    ) -> None:
        # Trigger on_change event
        try:
            new_value = delta_state["is_open"]
        except KeyError:
            pass
        else:
            assert isinstance(new_value, bool), new_value
            await self.call_event_handler(
                self.on_change,
                RevealerChangeEvent(new_value),
            )

    def _custom_serialize_(self) -> JsonDoc:
        # Serialization doesn't handle unions. Hence the custom serialization
        # here
        if isinstance(self.header_style, str):
            header_style = self.header_style
        else:
            header_style = self.header_style._serialize(self.session)

        return {
            "header_style": header_style,
        }


Revealer._unique_id_ = "Revealer-builtin"
