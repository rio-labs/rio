from __future__ import annotations

import enum
import typing as t
from datetime import timedelta

__all__ = [
    "on_mount",
    "on_page_change",
    "on_populate",
    "on_unmount",
    "on_window_size_change",
    "periodic",
]


R = t.TypeVar("R")
SyncOrAsync = R | t.Awaitable[R]
SyncOrAsyncNone = t.TypeVar("SyncOrAsyncNone", bound=SyncOrAsync[None])

Func = t.TypeVar("Func", bound=t.Callable)
Decorator = t.Callable[[Func], Func]

MethodWithNoParametersVar = t.TypeVar(
    "MethodWithNoParametersVar", bound=t.Callable[[t.Any], t.Any]
)


class EventTag(enum.Enum):
    """
    Event tags are internal markers used to keep track of which function needs
    to be called when.

    ## Metadata

    `public`: False
    """

    ON_MOUNT = enum.auto()
    ON_PAGE_CHANGE = enum.auto()
    ON_POPULATE = enum.auto()
    ON_UNMOUNT = enum.auto()
    ON_WINDOW_SIZE_CHANGE = enum.auto()
    PERIODIC = enum.auto()


def _tag_as_event_handler(
    function: t.Callable,
    tag: EventTag,
    args: t.Any,
) -> None:
    """
    Registers the function as an event handler for the given tag. This simply
    adds a marker to the function's `__dict__` so that it can later be
    recognized as an event handler.
    """
    all_events: dict[EventTag, list[t.Any]] = vars(function).setdefault(
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

    This decorator can be used on both synchronous as well as asynchronous
    methods.


    ## Example

    Here's an example of a component being conditionally included in the
    component tree. The `Switch` controls whether the `OnMountPrinter` exists or
    not, so turning on the switch will mount the `OnMountPrinter` and print
    "Mounted" to the console.

    ```python
    class OnMountPrinter(rio.Component):
        @rio.event.on_mount
        def on_mount(self):
            print("Mounted")

        def build(self):
            return rio.Text("hello")


    class Toggler(rio.Component):
        child: rio.Component
        show_child: bool = False

        def build(self) -> rio.Component:
            return rio.Column(
                # Depending on the Switch state, show either the
                # child or a placeholder
                self.child if self.show_child else rio.Text(""),
                rio.Switch(is_on=self.bind().show_child),
            )


    app = rio.App(build=lambda: Toggler(OnMountPrinter()))
    app.run_in_browser()
    ```


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
    when the page changes, you can combine this decorator with `__post_init__`
    or `on_populate`.

    This decorator can be used on both synchronous as well as asynchronous
    methods.


    ## Example

    ```python
    class UrlDisplay(rio.Component):
        current_url: rio.URL = rio.URL()

        def __post_init__(self):
            self.current_url = self.session.active_page_url

        @rio.event.on_page_change
        def on_page_change(self):
            self.current_url = self.session.active_page_url

        def build(self):
            return rio.Text(f"You're currently on {self.current_url}")
    ```


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

    This decorator can be used on both synchronous as well as asynchronous
    methods.


    ## Example

    `on_populate` is often useful as a sort of "async init", where you can put
    async code that needs to be run when the component is instantiated. In this
    example we'll use it to perform an asynchronous HTTP request.

    ```python
    import httpx
    import dataclasses


    class PypiVersionFetcher(rio.Component):
        module: str
        # The `version` attribute is initialized to an empty
        # string, which will will act as a placeholder until
        # the HTTP request finishes
        version: str = dataclasses.field(init=False, default="")

        @rio.event.on_populate
        async def on_populate(self):
            # Whenever this component is instantiated or
            # reconciled, fetch the version of the given module
            async with httpx.AsyncClient() as client:
                url = f"https://pypi.org/pypi/{self.module}/json"
                response = await client.get(url)
                self.version = response.json()["info"]["version"]

        def build(self):
            return rio.Text(f"Latest {self.module} version: {self.version}")
    ```


    ## Metadata

    `decorator`: True
    """

    _tag_as_event_handler(handler, EventTag.ON_POPULATE, None)
    return handler


def on_unmount(
    handler: MethodWithNoParametersVar,
) -> MethodWithNoParametersVar:
    """
    Triggered when the component is removed from the component tree.

    This decorator makes the decorated method an event handler for `on_unmount`
    events. The method will be called whenever the component is removed from the
    component tree.

    This may be triggered multiple times if the component is removed and then
    re-added.

    This decorator can be used on both synchronous as well as asynchronous
    methods.


    ## Example

    Here's an example of a component being conditionally included in the
    component tree. The `Switch` controls whether the `OnUnmountPrinter` exists
    or not, so turning on the switch will mount the `OnUnmountPrinter` and print
    "Unmounted" to the console.

    ```python
    class OnUnmountPrinter(rio.Component):
        @rio.event.on_unmount
        def on_unmount(self):
            print("Unmounted")

        def build(self):
            return rio.Text("hello")


    class Toggler(rio.Component):
        child: rio.Component
        show_child: bool = False

        def build(self) -> rio.Component:
            return rio.Column(
                # Depending on the Switch state, show either the
                # child or a placeholder
                self.child if self.show_child else rio.Text(""),
                rio.Switch(is_on=self.bind().show_child),
            )


    app = rio.App(build=lambda: Toggler(OnUnmountPrinter()))
    app.run_in_browser()
    ```


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

    This decorator can be used on both synchronous as well as asynchronous
    methods.


    ## Example

    We'll make a component that displays the size of the window. The
    `@window_size_change` event is used to rebuild the component whenever the
    window size changes. (This doesn't happen automatically because Rio only
    rebuilds components when their attributes change, and this component doesn't
    have any attributes that change.)

    ```python
    class WindowSizeDisplay(rio.Component):
        @rio.event.on_window_size_change
        def on_window_size_change(self) -> None:
            self.force_refresh()

        def build(self) -> rio.Component:
            width = self.session.window_width
            height = self.session.window_height
            return rio.Text(f"The window size is {width:.1f}x{height:.1f}")
    ```


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

    This decorator can be used on both synchronous as well as asynchronous
    methods.


    ## Parameters

    `interval`: The number of seconds, or timedelta, between each trigger.


    ## Example

    Here we use `@rio.event.periodic` to increment a counter every second:

    ```python
    class Counter(rio.Component):
        count: int = 0

        @rio.event.periodic(1)
        def increment_count(self):
            self.count += 1

        def build(self):
            return rio.Text(f"{self.count} seconds have passed")
    ```


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
