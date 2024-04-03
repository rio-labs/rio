"""
Contains processing specific to the RIO project.
"""

from typing import *  # type: ignore

import rio

from . import models


def find_items_needing_documentation() -> Iterable[Type | Callable]:
    """
    Find all classes and functions in `Rio` that need to be documented.
    """

    # Hardcoded items
    yield rio.App
    yield rio.AssetError
    yield rio.BoxStyle
    yield rio.Color
    yield rio.ColorChangeEvent
    yield rio.CursorStyle
    yield rio.DrawerOpenOrCloseEvent
    yield rio.DropdownChangeEvent
    yield rio.escape_markdown_code
    yield rio.escape_markdown
    yield rio.FileInfo
    yield rio.Font
    yield rio.KeyDownEvent
    yield rio.KeyPressEvent
    yield rio.KeyUpEvent
    yield rio.MouseDownEvent
    yield rio.MouseEnterEvent
    yield rio.MouseLeaveEvent
    yield rio.MouseMoveEvent
    yield rio.MouseUpEvent
    yield rio.NavigationFailed
    yield rio.NumberInputChangeEvent
    yield rio.NumberInputConfirmEvent
    yield rio.Page
    yield rio.PopupOpenOrCloseEvent
    yield rio.RevealerChangeEvent
    yield rio.Session
    yield rio.TextInputChangeEvent
    yield rio.TextInputConfirmEvent
    yield rio.TextStyle
    yield rio.Theme
    yield rio.UserSettings

    # Yield classes that also need their children documented
    to_do = [
        rio.Fill,
        rio.Component,
    ]

    while to_do:
        cur = to_do.pop()

        # Queue the children
        to_do.extend(cur.__subclasses__())

        # Hardcoded items that DON'T need documentation
        if cur.__name__ in (
            "ClassContainer",
            "FundamentalComponent",
            "RootContainer",
        ):
            continue

        # Skip anything not in the `rio` module
        if not cur.__module__.startswith("rio"):
            continue

        # Internal
        if not cur.__name__.startswith("_"):
            yield cur


def postprocess_class_docs(docs: models.ClassDocs) -> None:
    """
    Perform RIO specific post-processing on the component, such as stripping out
    internal attributes and functions.
    """

    # Strip default docstrings created by dataclasses
    if docs.summary is not None and docs.summary.startswith(f"{docs.name}("):
        docs.summary = None
        docs.details = None

    # Strip internal attributes
    index = 0
    while index < len(docs.attributes):
        attr = docs.attributes[index]

        # Decide whether to keep it
        keep = not attr.name.startswith("_")

        # Strip it out, if necessary
        if keep:
            index += 1
        else:
            del docs.attributes[index]

    # Skip internal functions
    index = 0
    while index < len(docs.functions):
        func = docs.functions[index]

        # Decide whether to keep it

        # Internal methods start with an underscore
        keep = not func.name.startswith("_")

        # Some methods in components are meant to be used by the user, but only
        # when they're the one creating the component. For example, the `build`
        # method is only intended to be used by the component itself, and
        # documenting it would be pointless at best, and confusing at worst.
        is_inherited_protected_method = docs.name != "Component" and func.name in (
            "build",
            "call_event_handler",
            "force_refresh",
        )
        keep = keep and not is_inherited_protected_method

        # Strip lambdas
        keep = keep and func.name != "<lambda>"

        # Make sure to keep the constructor
        keep = keep or func.name == "__init__"

        # Some classes are not meant to be constructed by the user. Strip their
        # constructor.
        if (
            docs.name
            in (
                "FileInfo",
                "Session",
            )
            and func.name == "__init__"
        ):
            keep = False

        # Strip it out, if necessary
        if keep:
            index += 1
        else:
            del docs.functions[index]

    # Additional per-function post-processing
    for func_docs in docs.functions:
        # Strip the ridiculous default docstring created by dataclasses
        #
        # FIXME: Not working for some reason
        if (
            func_docs.name == "__init__"
            and func_docs.summary
            == "Initialize self. See help(type(self)) for accurate signature."
        ):
            func_docs.summary = None
            func_docs.details = None

        # Inject a short description for `__init__` if there is none.
        if func_docs.name == "__init__" and func_docs.summary is None:
            func_docs.summary = f"Creates a new `{docs.name}` instance."

    # TODO: Strip out anything `Session` inherits from `unicall`


def postprocess_component_docs(docs: models.ClassDocs) -> None:
    # Apply the standard class post-processing
    postprocess_class_docs(docs)
