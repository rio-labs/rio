from __future__ import annotations

import enum
import typing as t
from dataclasses import dataclass

import imy.docstrings

import rio

__all__ = [
    "ExtensionAppStartEvent",
    "ExtensionAppCloseEvent",
    "ExtensionSessionStartEvent",
    "ExtensionSessionCloseEvent",
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

MethodWithAppStartEventParameterVar = t.TypeVar(
    "MethodWithAppStartEventParameterVar",
    bound=t.Callable[["ExtensionAppStartEvent"], t.Any],
)

MethodWithAppCloseEventParameterVar = t.TypeVar(
    "MethodWithAppCloseEventParameterVar",
    bound=t.Callable[["ExtensionAppCloseEvent"], t.Any],
)

MethodWithSessionStartEventParameterVar = t.TypeVar(
    "MethodWithSessionStartEventParameterVar",
    bound=t.Callable[["ExtensionSessionStartEvent"], t.Any],
)

MethodWithSessionCloseEventParameterVar = t.TypeVar(
    "MethodWithSessionCloseEventParameterVar",
    bound=t.Callable[["ExtensionSessionCloseEvent"], t.Any],
)

MethodWithPageChangeEventParameterVar = t.TypeVar(
    "MethodWithPageChangeEventParameterVar",
    bound=t.Callable[["ExtensionPageChangeEvent"], t.Any],
)


class ExtensionEventTag(enum.Enum):
    """
    Event tags are internal markers used to keep track of which function needs
    to be called when.

    ## Metadata

    `public`: False
    """

    ON_APP_START = enum.auto()
    ON_APP_CLOSE = enum.auto()

    ON_SESSION_START = enum.auto()
    ON_SESSION_CLOSE = enum.auto()

    ON_PAGE_CHANGE = enum.auto()


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclass
class ExtensionAppStartEvent:
    """
    TODO
    """

    pass


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclass
class ExtensionAppCloseEvent:
    """
    TODO
    """

    pass


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclass
class ExtensionSessionStartEvent:
    """
    TODO
    """

    session: rio.Session


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclass
class ExtensionSessionCloseEvent:
    """
    TODO
    """

    session: rio.Session


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclass
class ExtensionPageChangeEvent:
    """
    TODO
    """

    session: rio.Session


def _tag_as_event_handler(
    function: t.Callable,
    tag: ExtensionEventTag,
    args: t.Any,
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
    events_like_this.append(args)


def _collect_tagged_methods_recursive(
    cls: t.Type,
) -> dict[ExtensionEventTag, list[t.Callable]]:
    """
    Walks a class and its parents, gathering all methods that have been tagged
    as event handlers.

    The result is a dictionary where the keys are event tags and the values are
    lists of functions that are handlers for that event. If there aren't any
    handlers for a particular event, the result may have no entry for this tag
    at all, or contain an empty list.
    """
    result: dict[ExtensionEventTag, list[t.Callable]] = {}

    # The MRO conveniently includes all classes that need to be searched
    for base in cls.__mro__:
        # Walk all methods in the class
        for _, method in vars(base).items():
            # Skip untagged members. This also conveniently filters out any
            # non-callables, as they can't be tagged.
            if not hasattr(method, "_rio_extension_events_"):
                continue

            assert callable(method), method

            # Which events is this method a handler for?
            for tag, handlers in method._rio_extension_events_.items():
                result.setdefault(tag, []).extend(handlers)

    return result


def on_app_start(
    handler: MethodWithAppStartEventParameterVar,
) -> MethodWithAppStartEventParameterVar:
    """
    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_APP_START, None)
    return handler


def on_app_close(
    handler: MethodWithAppCloseEventParameterVar,
) -> MethodWithAppCloseEventParameterVar:
    """
    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_APP_CLOSE, None)
    return handler


def on_session_start(
    handler: MethodWithSessionStartEventParameterVar,
) -> MethodWithSessionStartEventParameterVar:
    """
    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_SESSION_START, None)
    return handler


def on_session_close(
    handler: MethodWithSessionCloseEventParameterVar,
) -> MethodWithSessionCloseEventParameterVar:
    """
    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_SESSION_CLOSE, None)
    return handler


def on_page_change(
    handler: MethodWithPageChangeEventParameterVar,
) -> MethodWithPageChangeEventParameterVar:
    """
    ## Metadata

    `decorator`: True
    """
    _tag_as_event_handler(handler, ExtensionEventTag.ON_PAGE_CHANGE, None)
    return handler
