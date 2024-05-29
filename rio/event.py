from __future__ import annotations

import enum
from datetime import timedelta
from typing import *  # type: ignore

__all__ = [
    "on_mount",
    "on_page_change",
    "on_populate",
    "on_unmount",
    "on_window_size_change",
    "periodic",
]


R = TypeVar("R")
SyncOrAsync = R | Awaitable[R]
SyncOrAsyncNone = TypeVar("SyncOrAsyncNone", bound=SyncOrAsync[None])

Func = TypeVar("Func", bound=Callable)
Decorator = Callable[[Func], Func]

MethodWithNoParametersVar = TypeVar(
    "MethodWithNoParametersVar", bound=Callable[[Any], Any]
)


class EventTag(enum.Enum):
    """
    Event tags are internal markers used to keep track of which function needs
    to be called when.

    ## Metadata

    public: False
    """

    ON_MOUNT = enum.auto()
    ON_PAGE_CHANGE = enum.auto()
    ON_POPULATE = enum.auto()
    ON_UNMOUNT = enum.auto()
    ON_WINDOW_SIZE_CHANGE = enum.auto()
    PERIODIC = enum.auto()


def _tag_as_event_handler(
    function: Callable,
    tag: EventTag,
    args: Any,
) -> None:
    """
    Registers the function as an event handler for the given tag. This simply
    adds a marker to the function's `__dict__` so that it can later be
    recognized as an event handler.
    """
    all_events: dict[EventTag, list[Any]] = vars(function).setdefault(
        "_rio_events_", {}
    )
    events_like_this = all_events.setdefault(tag, [])
    events_like_this.append(args)


def on_mount(handler: MethodWithNoParametersVar) -> MethodWithNoParametersVar:
    """
    Triggered when the component is added to the component tree.

    This decorator makes the decorated method an event handler for `on_mount`
    events. The method will be called whenever the component is added to the
    component tree.

    This may be triggered multiple times if the component is removed and then
    re-added.


    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, EventTag.ON_MOUNT, None)
    return handler


def on_page_change(
    handler: MethodWithNoParametersVar,
) -> MethodWithNoParametersVar:
    """
    Triggered whenever the session changes pages.

    Makes the decorated method an event handler for `on_page_change` events.
    The method will be called whenever the session navigates to a new page.

    If you want your code to run both when the component was first created _and_
    when the page changes, you can combine this decorator with `on_populate`.


    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, EventTag.ON_PAGE_CHANGE, None)
    return handler


def on_populate(
    handler: MethodWithNoParametersVar,
) -> MethodWithNoParametersVar:
    """
    Triggered when the component has been created or has been reconciled.

    This decorator makes the decorated method an event handler for `on_populate`
    events. The method will be called whenever the component has been created or
    has been reconciled. This allows you to asynchronously fetch any data right
    after component initialization.


    ## Metadata

    `decorator`: True
    """

    _tag_as_event_handler(handler, EventTag.ON_POPULATE, None)
    return handler


def on_unmount(handler: MethodWithNoParametersVar) -> MethodWithNoParametersVar:
    """
    Triggered when the component is removed from the component tree.

    This decorator makes the decorated method an event handler for `on_unmount`
    events. The method will be called whenever the component is removed from the
    component tree.

    This may be triggered multiple times if the component is removed and then
    re-added.


    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, EventTag.ON_UNMOUNT, None)
    return handler


def on_window_size_change(
    handler: MethodWithNoParametersVar,
) -> MethodWithNoParametersVar:
    """
    Triggered when the client's window is resized.

    This decorator makes the decorated method an event handler for
    `on_window_size_change` events. The method will be called whenever the
    window changes size. You can access the window's size using
    `self.session.window_width` and `self.session.window_height` as usual.

    Some of the ways that a window can resize are non obvious. For example,
    rotating a mobile device will trigger this event, since width and height
    trade places. This event may also be triggered when the browser's dev tools
    are opened or closed, or when the browser's zoom level is changed, since all
    of those impact the available screen space.


    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, EventTag.ON_WINDOW_SIZE_CHANGE, None)
    return handler


def periodic(
    interval: float | timedelta,
) -> Decorator[MethodWithNoParametersVar]:
    """
    Triggered at a fixed time interval.

    This decorator causes the decorated method to be called repeatedly at a
    fixed time interval. The event will be triggered for as long as the
    component exists, even if it is not mounted. The interval can be specified
    as either a number of seconds or as a timedelta.

    The interval only starts counting after the previous handler has finished
    executing, so the handler will never run twice simultaneously, even if it
    takes longer than the interval to execute.


    ## Parameters

    `interval`: The number of seconds, or timedelta, between each trigger.


    ## Metadata

    `decorator`: True
    `experimental`: True
    """
    # Convert timedelta to float
    if isinstance(interval, timedelta):
        interval = interval.total_seconds()

    def decorator(
        handler: MethodWithNoParametersVar,
    ) -> MethodWithNoParametersVar:
        _tag_as_event_handler(handler, EventTag.PERIODIC, interval)
        return handler

    return decorator
