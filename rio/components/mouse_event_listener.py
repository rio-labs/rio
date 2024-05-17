from __future__ import annotations

import enum
from dataclasses import KW_ONLY, dataclass
from typing import *  # type: ignore

from uniserde import JsonDoc

import rio.docs

from .fundamental_component import FundamentalComponent

__all__ = [
    "MouseEventListener",
    "MouseButton",
    "PressEvent",
    "MouseDownEvent",
    "MouseUpEvent",
    "MouseMoveEvent",
    "MouseEnterEvent",
    "MouseLeaveEvent",
    "DragStartEvent",
    "DragMoveEvent",
    "DragEndEvent",
]


@final
class MouseButton(enum.Enum):
    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"


@dataclass
class _ButtonEvent:
    button: MouseButton


@dataclass
class _PositionedEvent:
    """
    ## Attributes

    `x`: The x coordinate of the mouse when the event was triggered, relative to
        the left side of the window.

    `y`: The y coordinate of the mouse when the event was triggered, relative to
        the top of the window. (So a larger `y` means further down.)
    """

    x: float
    y: float


@final
@rio.docs.mark_constructor_as_private
@dataclass
class PressEvent(_ButtonEvent, _PositionedEvent):
    """
    Holds information regarding a mouse press event.

    This is a simple dataclass that stores useful information for when the user
    presses a mouse button. You'll typically receive this as argument in
    `on_press` events.

    ## Attributes

    `button`: The mouse button that was pressed.
    """


@final
@rio.docs.mark_constructor_as_private
@dataclass
class MouseDownEvent(_ButtonEvent, _PositionedEvent):
    """
    Holds information regarding a mouse down event.

    This is a simple dataclass that stores useful information for when the user
    presses a mouse button. You'll typically receive this as argument in
    `on_mouse_down` events.

    ## Attributes

    `button`: The mouse button that was pressed.
    """


@final
@rio.docs.mark_constructor_as_private
@dataclass
class MouseUpEvent(_ButtonEvent, _PositionedEvent):
    """
    Holds information regarding a mouse up event.

    This is a simple dataclass that stores useful information for when the user
    releases a mouse button. You'll typically receive this as argument in
    `on_mouse_up` events.

    ## Attributes

    `button`: The mouse button that was released.
    """


@final
@rio.docs.mark_constructor_as_private
class MouseMoveEvent(_PositionedEvent):
    """
    Holds information regarding a mouse move event.

    This is a simple dataclass that stores useful information for when the user
    moves the mouse. You'll typically receive this as argument in
    `on_mouse_move` events.
    """


@final
@rio.docs.mark_constructor_as_private
class MouseEnterEvent(_PositionedEvent):
    """
    Holds information regarding a mouse enter event.

    This is a simple dataclass that stores useful information for when the user
    moves the mouse over a component. You'll typically receive this as argument
    in `on_mouse_enter` events.
    """


@final
@rio.docs.mark_constructor_as_private
class MouseLeaveEvent(_PositionedEvent):
    """
    Holds information regarding a mouse leave event.

    This is a simple dataclass that stores useful information for when the user
    moves the mouse away from a component. You'll typically receive this as
    argument in `on_mouse_leave` events.
    """


@dataclass
class _DragEvent(_ButtonEvent, _PositionedEvent):
    """
    Holds information regarding a drag event.

    This is a simple dataclass that stores useful information for when the user
    drags the mouse. You'll typically receive this as argument in
    `on_drag_start`, `on_drag_move`, and `on_drag_end` events.

    ## Attributes

    `component`: The component located under the mouse cursor when the event
        happened.
    """

    component: rio.Component


@final
@rio.docs.mark_constructor_as_private
class DragStartEvent(_DragEvent):
    """
    Holds information regarding a drag start event.

    This is a simple dataclass that stores useful information for when the user
    starts dragging the mouse. You'll typically receive this as argument in
    `on_drag_start` events.
    """


@final
@rio.docs.mark_constructor_as_private
class DragMoveEvent(_DragEvent):
    """
    Holds information regarding a drag move event.

    This is a simple dataclass that stores useful information for when the user
    moves the mouse while dragging. You'll typically receive this as argument in
    `on_drag_move` events.
    """


@final
@rio.docs.mark_constructor_as_private
class DragEndEvent(_DragEvent):
    """
    Holds information regarding a drag end event.

    This is a simple dataclass that stores useful information for when the user
    stops dragging the mouse. You'll typically receive this as argument in
    `on_drag_end` events.
    """


@final
class MouseEventListener(FundamentalComponent):
    """
    Allows you to listen for mouse events on a component.

    `MouseEventListeners` take a single child component and display it. They
    then listen for any mouse activity on the child component and report it
    through their event handlers.


    ## Attributes

    `content`: The child component to display.

    `on_press`: Similar to `on_mouse_up`, but performs additional subtle
        checks, such as that the left mouse button was pressed.

    `on_mouse_down`: Triggered when a mouse button is pressed down while
        the mouse is placed over the child component.

    `on_mouse_up`: Triggered when a mouse button is released while the
        mouse is placed over the child component.

    `on_mouse_move`: Triggered when the mouse is moved while located over
        the child component.

    `on_mouse_enter`: Triggered when the mouse previously was not located
        over the child component, but now is.

    `on_mouse_leave`: Triggered when the mouse previously was located over
        the child component, but now is not.

    `on_drag_start`: Triggered when the user starts dragging the mouse, i.e.
        moving it while holding down a mouse button.

    `on_drag_move`: Triggered when the user moves the mouse while holding down a
        mouse button.

    `on_drag_end`: Triggered then the user stops dragging the mouse.
    """

    content: rio.Component
    _: KW_ONLY
    on_press: rio.EventHandler[PressEvent] = None
    on_mouse_down: rio.EventHandler[MouseDownEvent] = None
    on_mouse_up: rio.EventHandler[MouseUpEvent] = None
    on_mouse_move: rio.EventHandler[MouseMoveEvent] = None
    on_mouse_enter: rio.EventHandler[MouseEnterEvent] = None
    on_mouse_leave: rio.EventHandler[MouseLeaveEvent] = None
    on_drag_start: rio.EventHandler[DragStartEvent] = None
    on_drag_move: rio.EventHandler[DragMoveEvent] = None
    on_drag_end: rio.EventHandler[DragEndEvent] = None

    def _custom_serialize(self) -> JsonDoc:
        return {
            "reportPress": self.on_press is not None,
            "reportMouseDown": self.on_mouse_down is not None,
            "reportMouseUp": self.on_mouse_up is not None,
            "reportMouseMove": self.on_mouse_move is not None,
            "reportMouseEnter": self.on_mouse_enter is not None,
            "reportMouseLeave": self.on_mouse_leave is not None,
            "reportDragStart": self.on_drag_start is not None,
            "reportDragMove": self.on_drag_move is not None,
            "reportDragEnd": self.on_drag_end is not None,
        }

    async def _on_message(self, msg: Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg

        msg_type = msg["type"]
        assert isinstance(msg_type, str), msg_type

        # Dispatch the correct event
        if msg_type == "press":
            await self.call_event_handler(
                self.on_press,
                PressEvent(
                    x=msg["x"],
                    y=msg["y"],
                    button=MouseButton(msg["button"]),
                ),
            )

        elif msg_type == "mouseDown":
            await self.call_event_handler(
                self.on_mouse_down,
                MouseDownEvent(
                    x=msg["x"],
                    y=msg["y"],
                    button=MouseButton(msg["button"]),
                ),
            )

        elif msg_type == "mouseUp":
            await self.call_event_handler(
                self.on_mouse_up,
                MouseUpEvent(
                    x=msg["x"],
                    y=msg["y"],
                    button=MouseButton(msg["button"]),
                ),
            )

        elif msg_type == "mouseMove":
            await self.call_event_handler(
                self.on_mouse_move,
                MouseMoveEvent(
                    x=msg["x"],
                    y=msg["y"],
                ),
            )

        elif msg_type == "mouseEnter":
            await self.call_event_handler(
                self.on_mouse_enter,
                MouseEnterEvent(
                    x=msg["x"],
                    y=msg["y"],
                ),
            )

        elif msg_type == "mouseLeave":
            await self.call_event_handler(
                self.on_mouse_leave,
                MouseLeaveEvent(
                    x=msg["x"],
                    y=msg["y"],
                ),
            )

        elif msg_type == "dragStart":
            await self.call_event_handler(
                self.on_drag_start,
                DragStartEvent(
                    button=msg["button"],
                    x=msg["x"],
                    y=msg["y"],
                    component=self.session._weak_components_by_id[
                        msg["component"]
                    ],
                ),
            )

        elif msg_type == "dragMove":
            await self.call_event_handler(
                self.on_drag_move,
                DragMoveEvent(
                    button=msg["button"],
                    x=msg["x"],
                    y=msg["y"],
                    component=self.session._weak_components_by_id[
                        msg["component"]
                    ],
                ),
            )

        elif msg_type == "dragEnd":
            await self.call_event_handler(
                self.on_drag_end,
                DragEndEvent(
                    button=msg["button"],
                    x=msg["x"],
                    y=msg["y"],
                    component=self.session._weak_components_by_id[
                        msg["component"]
                    ],
                ),
            )

        else:
            raise ValueError(
                f"{__class__.__name__} encountered unknown message: {msg}"
            )

        # Refresh the session
        await self.session._refresh()


MouseEventListener._unique_id = "MouseEventListener-builtin"
