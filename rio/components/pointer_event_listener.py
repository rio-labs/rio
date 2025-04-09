from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import Jsonable, JsonDoc

import rio

from .fundamental_component import FundamentalComponent

__all__ = [
    "PointerEvent",
    "PointerMoveEvent",
    "PointerEventListener",
]


MouseButton = t.Literal["left", "middle", "right"]
MOUSE_BUTTONS = t.get_args(MouseButton)


@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class PointerEvent:
    """
    Holds information regarding a pointer event.

    This is a simple dataclass that stores useful information for when the user
    interacts with a component using a mouse, touch, or other pointer-style
    device. You'll receive this as argument in a variety of pointer events.


    ## Attributes

    `pointer_type`: What sort of pointer triggered the event. Can be either
        `"mouse"` or `"touch"`.

    `button`: The mouse button that was pressed, if any. For mouse events
        (`pointer_type=="mouse"`), this is either `"left"`, `"middle"`, or
        `"right"`. For other events, this is `None`.

    `window_x`: The x coordinate of the pointer relative to the window. The
        origin is the top-left corner of the window, with larger `x` values
        meaning further to the right.

    `window_y`: The y coordinate of the pointer relative to the window. The
        origin is the top-left corner of the window, with larger `y` values
        meaning further down.

    `component_x`: The x coordinate of the pointer relative to the
        `PointerEventListener` component. The origin is the top-left corner of
        the component, with larger `x` values meaning further to the right.

    `component_y`: The y coordinate of the pointer relative to the
        `PointerEventListener` component. The origin is the top-left corner of
        the component, with larger `y` values meaning further down.
    """

    pointer_type: t.Literal["mouse", "touch"]

    button: MouseButton | None

    window_x: float
    window_y: float

    component_x: float
    component_y: float

    @staticmethod
    def _from_message(msg: dict[str, t.Any]) -> PointerEvent:
        result = PointerEvent(
            pointer_type=msg["pointerType"],
            button=msg.get("button"),
            window_x=msg["windowX"],
            window_y=msg["windowY"],
            component_x=msg["componentX"],
            component_y=msg["componentY"],
        )

        assert result.pointer_type in ("mouse", "touch")
        assert result.button is None or result.button in MOUSE_BUTTONS
        assert isinstance(result.window_x, (int, float))
        assert isinstance(result.window_y, (int, float))
        assert isinstance(result.component_x, (int, float))
        assert isinstance(result.component_y, (int, float))

        return result


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class PointerMoveEvent(PointerEvent):
    """
    Holds information regarding a pointer move event.

    This is a simple dataclass that stores useful information for when the user
    moves the pointer. You'll typically receive this as argument in
    `on_pointer_move` events.


    ## Attributes

    `relative_x`: How far the pointer has moved horizontally since the last
        time the event was triggered.

    `relative_y`: How far the pointer has moved vertically since the last time
        the event was triggered.
    """

    relative_x: float
    relative_y: float

    @staticmethod
    def _from_message(msg: dict[str, t.Any]) -> PointerMoveEvent:
        return PointerMoveEvent(
            pointer_type=msg["pointerType"],
            button=msg.get("button"),
            window_x=msg["windowX"],
            window_y=msg["windowY"],
            component_x=msg["componentX"],
            component_y=msg["componentY"],
            relative_x=msg["relativeX"],
            relative_y=msg["relativeY"],
        )


@t.final
class PointerEventListener(FundamentalComponent):
    """
    Allows you to listen for mouse & touch events on a component.

    `PointerEventListener` takes a single child component and displays it. It
    then listens for any mouse and touch activity on the child component and
    reports it through its events.


    ## Attributes

    `content`: The child component to display and watch.

    `on_press`: Similar to `on_pointer_up`, but performs additional subtle
        checks, such as that the pressed mouse button was the left one.

    `on_double_press`: Similar to `on_press`, but triggered when the mouse
        button is double-pressed.

    `on_pointer_down`: Triggered when a pointer button is pressed down while
        the pointer is placed over the child component.

    `on_pointer_up`: Triggered when a pointer button is released while the
        pointer is placed over the child component.

    `on_pointer_move`: Triggered when the pointer is moved while located over
        the child component.

    `on_pointer_enter`: Triggered when the pointer previously was not located
        over the child component, but is now.

    `on_pointer_leave`: Triggered when the pointer previously was located over
        the child component, but is no longer.

    `on_drag_start`: Triggered when the user starts dragging the pointer, i.e.
        moving it while holding down a pointer button.

    `on_drag_move`: Triggered when the user moves the pointer while holding down
        a pointer button. Note that once a drag event was triggered on a
        component, the move event will continue to fire even if the pointer
        leaves the component.

    `on_drag_end`: Triggered when the user stops dragging the pointer.
    """

    content: rio.Component
    _: dataclasses.KW_ONLY
    on_press: rio.EventHandler[PointerEvent] = None
    on_double_press: rio.EventHandler[PointerEvent] = None
    on_pointer_down: (
        rio.EventHandler[PointerEvent]
        | dict[MouseButton, rio.EventHandler[PointerEvent]]
    ) = None
    on_pointer_up: (
        rio.EventHandler[PointerEvent]
        | dict[MouseButton, rio.EventHandler[PointerEvent]]
    ) = None
    on_pointer_move: rio.EventHandler[PointerMoveEvent] = None
    on_pointer_enter: rio.EventHandler[PointerEvent] = None
    on_pointer_leave: rio.EventHandler[PointerEvent] = None
    on_drag_start: rio.EventHandler[PointerEvent] = None
    on_drag_move: rio.EventHandler[PointerMoveEvent] = None
    on_drag_end: rio.EventHandler[PointerEvent] = None

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "reportPress": self.on_press is not None,
            "reportDoublePress": self.on_double_press is not None,
            "reportPointerDown": _list_buttons_to_report(self.on_pointer_down),
            "reportPointerUp": _list_buttons_to_report(self.on_pointer_up),
            "reportPointerMove": self.on_pointer_move is not None,
            "reportPointerEnter": self.on_pointer_enter is not None,
            "reportPointerLeave": self.on_pointer_leave is not None,
            "reportDragStart": self.on_drag_start is not None,
            "reportDragMove": self.on_drag_move is not None,
            "reportDragEnd": self.on_drag_end is not None,
        }

    async def _on_message_(self, msg: t.Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg

        msg_type = msg["type"]
        assert isinstance(msg_type, str), msg_type

        # Dispatch the correct event
        if msg_type == "press":
            event = PointerEvent._from_message(msg)
            assert event.button == "left"
            await self.call_event_handler(self.on_press, event)

        elif msg_type == "doublePress":
            event = PointerEvent._from_message(msg)
            assert event.button == "left"
            await self._call_appropriate_event_handler(
                self.on_double_press, event
            )

        elif msg_type == "pointerDown":
            await self._call_appropriate_event_handler(
                self.on_pointer_down,
                PointerEvent._from_message(msg),
            )

        elif msg_type == "pointerUp":
            await self._call_appropriate_event_handler(
                self.on_pointer_up,
                PointerEvent._from_message(msg),
            )

        elif msg_type == "pointerMove":
            await self.call_event_handler(
                self.on_pointer_move,
                PointerMoveEvent._from_message(msg),
            )

        elif msg_type == "pointerEnter":
            await self.call_event_handler(
                self.on_pointer_enter,
                PointerEvent._from_message(msg),
            )

        elif msg_type == "pointerLeave":
            await self.call_event_handler(
                self.on_pointer_leave,
                PointerEvent._from_message(msg),
            )

        elif msg_type == "dragStart":
            await self.call_event_handler(
                self.on_drag_start,
                PointerEvent._from_message(msg),
            )

        elif msg_type == "dragMove":
            await self.call_event_handler(
                self.on_drag_move,
                PointerMoveEvent._from_message(msg),
            )

        elif msg_type == "dragEnd":
            await self.call_event_handler(
                self.on_drag_end,
                PointerEvent._from_message(msg),
            )

        else:
            raise ValueError(
                f"{__class__.__name__} encountered unknown message: {msg}"
            )

    async def _call_appropriate_event_handler(
        self,
        handler: rio.EventHandler[PointerEvent]
        | dict[MouseButton, rio.EventHandler[PointerEvent]],
        event: PointerEvent,
    ) -> None:
        if handler is None:
            return

        if not callable(handler):
            try:
                handler = handler[event.button]  # type: ignore (button can be None)
            except KeyError:
                return

        await self.call_event_handler(handler, event)


PointerEventListener._unique_id_ = "PointerEventListener-builtin"


def _list_buttons_to_report(
    handler: rio.EventHandler[PointerEvent]
    | dict[MouseButton, rio.EventHandler[PointerEvent]],
) -> Jsonable:
    if handler is None:
        return []

    if callable(handler):
        return MOUSE_BUTTONS

    return list(handler)
