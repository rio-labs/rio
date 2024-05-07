from __future__ import annotations

import enum
from datetime import timedelta
from typing import *  # type: ignore

__all__ = [
    "on_page_change",
    "on_mount",
    "on_unmount",
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

    ON_POPULATE = enum.auto()
    ON_PAGE_CHANGE = enum.auto()
    ON_MOUNT = enum.auto()
    ON_UNMOUNT = enum.auto()
    PERIODIC = enum.auto()


def _register_as_event_handler(
    function: Callable, tag: EventTag, args: Any
) -> None:
    all_events: dict[EventTag, list[Any]] = vars(function).setdefault(
        "_rio_events_", {}
    )
    events_like_this = all_events.setdefault(tag, [])
    events_like_this.append(args)


def on_populate(
    handler: MethodWithNoParametersVar,
) -> MethodWithNoParametersVar:
    """
    Triggered after the component has been created or has been reconciled. This
    allows you to asynchronously fetch any data which depends on the component's
    state.
    """
    _register_as_event_handler(handler, EventTag.ON_POPULATE, None)
    return handler


def on_page_change(
    handler: MethodWithNoParametersVar,
) -> MethodWithNoParametersVar:
    """
    Triggered whenever the session changes pages.
    """
    _register_as_event_handler(handler, EventTag.ON_PAGE_CHANGE, None)
    return handler


def on_mount(handler: MethodWithNoParametersVar) -> MethodWithNoParametersVar:
    """
    Triggered when the component is added to the component tree.

    This may be triggered multiple times if the component is removed and then
    re-added.
    """
    _register_as_event_handler(handler, EventTag.ON_MOUNT, None)
    return handler


def on_unmount(handler: MethodWithNoParametersVar) -> MethodWithNoParametersVar:
    """
    Triggered when the component is removed from the component tree.

    This may be triggered multiple times if the component is removed and then
    re-added.
    """
    _register_as_event_handler(handler, EventTag.ON_UNMOUNT, None)
    return handler


def periodic(
    interval: float | timedelta,
) -> Decorator[MethodWithNoParametersVar]:
    """
    This event is triggered repeatedly at a fixed time interval for as long as
    the component exists. The component does not have to be mounted for this
    event to trigger.

    The interval only starts counting after the previous handler has finished
    executing, so the handler will never run twice simultaneously, even if it
    takes longer than the interval to execute.


    ## Parameters

    `period`: The number of seconds, or timedelta, between each trigger.


    ## Metadata

    `experimental`: True
    """
    # Convert timedelta to float
    if isinstance(interval, timedelta):
        interval = interval.total_seconds()

    def decorator(
        handler: MethodWithNoParametersVar,
    ) -> MethodWithNoParametersVar:
        _register_as_event_handler(handler, EventTag.PERIODIC, interval)
        return handler

    return decorator
