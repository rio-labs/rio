from __future__ import annotations

import dataclasses
import enum
import typing as t

import fastapi
import imy.docstrings

import rio

__all__ = [
    "ExtensionAppStartEvent",
    "ExtensionAppCloseEvent",
    "ExtensionSessionStartEvent",
    "ExtensionSessionCloseEvent",
    "on_as_fastapi",
    "on_app_start",
    "on_app_close",
    "on_session_start",
    "on_session_close",
    "on_page_change",
]


R = t.TypeVar("R")
SyncOrAsync = R | t.Awaitable[R]
SyncOrAsyncNone = t.TypeVar("SyncOrAsyncNone", bound=SyncOrAsync[None])

Func = t.TypeVar("Func", bound=t.Callable)
Decorator = t.Callable[[Func], Func]

MethodWithNoParametersVar = t.TypeVar(
    "MethodWithNoParametersVar",
    bound=t.Callable[[t.Any], t.Any],
)

MethodWithAsFastapiParameterVar = t.TypeVar(
    "MethodWithAsFastapiParameterVar",
    bound=t.Callable[
        [t.Any, "ExtensionAsFastapiEvent"],
        # Note that this, and only this event requires a synchronous event
        # handler. Because of this, the function is annotated as having to
        # return `None`, so that asynchronous functions are highlighted by
        # linters.
        #
        # This prevents the function from returning anything else, or doing
        # something synchronously and _then_ returning an awaitable. That is a
        # very unlikely use of this function though, and so highlighting
        # mistakes is probably a good thing.
        None,
    ],
)

MethodWithAppStartEventParameterVar = t.TypeVar(
    "MethodWithAppStartEventParameterVar",
    bound=t.Callable[[t.Any, "ExtensionAppStartEvent"], t.Any],
)

MethodWithAppCloseEventParameterVar = t.TypeVar(
    "MethodWithAppCloseEventParameterVar",
    bound=t.Callable[[t.Any, "ExtensionAppCloseEvent"], t.Any],
)

MethodWithSessionStartEventParameterVar = t.TypeVar(
    "MethodWithSessionStartEventParameterVar",
    bound=t.Callable[[t.Any, "ExtensionSessionStartEvent"], t.Any],
)

MethodWithSessionCloseEventParameterVar = t.TypeVar(
    "MethodWithSessionCloseEventParameterVar",
    bound=t.Callable[[t.Any, "ExtensionSessionCloseEvent"], t.Any],
)

MethodWithPageChangeEventParameterVar = t.TypeVar(
    "MethodWithPageChangeEventParameterVar",
    bound=t.Callable[[t.Any, "ExtensionPageChangeEvent"], t.Any],
)


class ExtensionEventTag(enum.Enum):
    """
    Event tags are internal markers used to keep track of which function needs
    to be called when.

    ## Metadata

    `public`: False
    """

    ON_AS_FASTAPI = enum.auto()

    ON_APP_START = enum.auto()
    ON_APP_CLOSE = enum.auto()

    ON_SESSION_START = enum.auto()
    ON_SESSION_CLOSE = enum.auto()

    ON_PAGE_CHANGE = enum.auto()


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class ExtensionAsFastapiEvent:
    """
    Holds information regarding an extension as_fastapi event.

    This is a simple dataclass that stores useful information for when a Rio
    app creates its internal FastAPI app. You'll typically receive this as
    argument in `on_as_fastapi` events.

    ## Attributes

    `rio_app`: The Rio app that is being converted to FastAPI.

    `fastapi_app`: The FastAPI app that the Rio app is being converted to.

    ## Metadata

    `public`: False
    """

    rio_app: rio.App
    fastapi_app: fastapi.FastAPI


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class ExtensionAppStartEvent:
    """
    Holds information regarding an extension app start event.

    This is a simple dataclass that stores useful information for when an app
    starts up. You'll typically receive this as argument in `on_app_start`
    events.

    ## Attributes

    `app`: The app that is starting up.

    ## Metadata

    `public`: False
    """

    app: rio.App


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class ExtensionAppCloseEvent:
    """
    Holds information regarding an extension app close event.

    This is a simple dataclass that stores useful information for when an app
    closes down. You'll typically receive this as argument in `on_app_close`
    events.

    ## Attributes

    `app`: The app that is shutting down.

    ## Metadata

    `public`: False
    """

    app: rio.App


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class ExtensionSessionStartEvent:
    """
    Holds information regarding a session start event.

    This is a simple dataclass that stores useful information for when a session
    is started in an app that this extension is part of. You'll typically
    receive this as argument in `on_session_start` events.

    ## Attributes

    `session`: The session that was just started.

    ## Metadata

    `public`: False
    """

    session: rio.Session


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class ExtensionSessionCloseEvent:
    """
    Holds information regarding a session close event.

    This is a simple dataclass that stores useful information for when a session
    is closed in an app that this extension is part of. You'll typically receive
    this as argument in `on_session_close` events.

    ## Attributes

    `session`: The session that was just closed.

    ## Metadata

    `public`: False
    """

    session: rio.Session


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass
class ExtensionPageChangeEvent:
    """
    Holds information regarding a page change event.

    This is a simple dataclass that stores useful information for when the user
    navigates to a new page in an app that this extension is part of. You'll
    typically receive this as argument in `on_page_change` events.

    ## Attributes

    `session`: The session that the page change happened in.

    ## Metadata

    `public`: False
    """

    session: rio.Session


def _tag_as_event_handler(
    function: t.Callable,
    tag: ExtensionEventTag,
    arg: t.Any,
) -> None:
    """
    Registers the function as an event handler for the given tag. This simply
    adds a marker to the function's `__dict__` so that it can later be
    recognized as an event handler.
    """
    all_events: dict[ExtensionEventTag, list[t.Any]] = vars(
        function
    ).setdefault("_rio_extension_events_", {})

    events_like_this = all_events.setdefault(tag, [])
    events_like_this.append((function, arg))


def _collect_tagged_methods_recursive(
    ext: rio.Extension,
) -> dict[ExtensionEventTag, list[tuple[t.Callable, t.Any]]]:
    """
    Walks a class and its parents, gathering all methods that have been tagged
    as event handlers.

    The result is a dictionary where the keys are event tags and the values are
    lists of functions that are handlers for that event. If there aren't any
    handlers for a particular event, the result may have no entry for this tag
    at all, or contain an empty list.
    """
    result: dict[ExtensionEventTag, list[tuple[t.Callable, t.Any]]] = {}

    # The MRO conveniently includes all classes that need to be searched
    for base in type(ext).__mro__:
        # Walk all methods in the class
        for _, method in vars(base).items():
            # Skip untagged members. This also conveniently filters out any
            # non-callables, as they can't be tagged.
            if not hasattr(method, "_rio_extension_events_"):
                continue

            assert callable(method), method

            # Which events is this method a handler for?
            for tag, handlers in method._rio_extension_events_.items():
                # Because the method was retrieved from the class instead of an
                # instance, it's not bound to anything. Fix that.
                result.setdefault(tag, []).extend(
                    [
                        (
                            handler.__get__(ext),
                            arg,
                        )
                        for handler, arg in handlers
                    ]
                )

    return result


def on_as_fastapi(
    handler: MethodWithAsFastapiParameterVar,
) -> MethodWithAsFastapiParameterVar:
    """
    Triggered when the Rio app is converted to a FastAPI app.

    Internally, all Rio apps use FastAPI to host their internal API. You can
    explicitly get that FastAPI instance by calling `rio.App.as_fastapi`.
    However, even when you don't do this, and run the app via `rio run`,
    `rio.App.run_in_browser` or similar, a FastAPI app is still created
    internally.

    This event allows you to access that FastAPI app, and modify it before it's
    run. For example, you can use this to add routes and middleware to the app.

    Note that unlike most other events, this one requires a synchronous event
    handler. That's because `rio.App.as_fastapi` is a synchronous method and is
    thus unable to trigger asynchronous event handlers.

    ## Metadata

    `decorator`: True

    `public`: False
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_AS_FASTAPI, None)
    return handler


def on_app_start(
    handler: MethodWithAppStartEventParameterVar,
) -> MethodWithAppStartEventParameterVar:
    """
    Triggered when the app starts up.

    This event is triggered when an app that this extension is part of is
    starting up. You can use this to e.g. connect to your database, and add the
    database connection to the app's default attachments. This way all sessions
    will have access to it as attachments.

    ## Metadata

    `decorator`: True

    `public`: False
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_APP_START, None)
    return handler


def on_app_close(
    handler: MethodWithAppCloseEventParameterVar,
) -> MethodWithAppCloseEventParameterVar:
    """
    Triggered when the app is shutting down.

    This event is triggered when an app that this extension is part of is
    shutting down. You can use this to e.g. close any database connections or
    HTTP clients that you've opened during the app's lifetime.

    ## Metadata

    `decorator`: True

    `public`: False
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_APP_CLOSE, None)
    return handler


def on_session_start(
    handler: MethodWithSessionStartEventParameterVar,
) -> MethodWithSessionStartEventParameterVar:
    """
    Triggered when a new session is created.

    This event is triggered when a new session is created in an app that this
    extension is part of. You can use this to e.g. read the user's settings or
    attach objects to the session.

    ## Metadata

    `decorator`: True

    `public`: False
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_SESSION_START, None)
    return handler


def on_session_close(
    handler: MethodWithSessionCloseEventParameterVar,
) -> MethodWithSessionCloseEventParameterVar:
    """
    Triggered when a session is closed.

    This event is triggered when a session is closed in an app that this
    extension is part of. You can use this to e.g. save latent settings or clean
    up any resources that were attached to the session.
    ## Metadata

    `decorator`: True

    `public`: False
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_SESSION_CLOSE, None)
    return handler


def on_page_change(
    handler: MethodWithPageChangeEventParameterVar,
) -> MethodWithPageChangeEventParameterVar:
    """
    Triggered when the user navigates to a new page.

    This event is triggered when the user navigates to a new page in an app that
    this extension is part of. You can use this e.g. for analytics, or to
    pre-fetch data for the new page.

    ## Metadata

    `decorator`: True

    `public`: False
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_PAGE_CHANGE, None)
    return handler
