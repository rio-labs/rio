"""
Contains documentation related tasks specific to the Rio project.
"""

import dataclasses
import inspect
from typing import *  # type: ignore

import imy.docstrings

import rio

__all__ = [
    "get_documentation_fragment",
    "build_documentation_url",
    "find_documented_objects",
    "postprocess_function_docs",
    "postprocess_class_docs",
    "postprocess_component_docs",
]


def get_documentation_fragment(object_name: str) -> str:
    """
    Returns the fragment part of the URL corresponding to the documentation for
    the given Rio object.
    """
    return object_name.lower()


def build_documentation_url(
    object_name: str,
    *,
    relative: bool = False,
) -> rio.URL:
    """
    Returns the URL to the documentation for the given Rio object. This doesn't
    perform any checks on whether the object actually exists and has
    documentation. It relies solely on the passed values.
    """

    # Build the relative URL
    result_string = f"/docs/api/{get_documentation_fragment(object_name)}"

    # Make it absolute, if requested
    if not relative:
        result_string = "https://rio.dev" + result_string

    # Done
    return rio.URL(result_string)


def _find_possibly_public_objects() -> Iterable[Type | Callable]:
    """
    Finds all objects in rio that might be public. This uses heuristics to
    filter out many internal objects, but it's not perfect.
    """
    # Hardcoded items
    yield rio.App
    yield rio.AssetError
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
        if not cur.__module__.startswith("rio."):
            continue

        # Internal
        if cur.__name__.startswith("_"):
            continue

        yield cur


def find_documented_objects(
    postprocess: bool,
) -> Iterable[
    tuple[Type, imy.docstrings.ClassDocs]
    | tuple[Callable, imy.docstrings.FunctionDocs],
]:
    """
    Find all public classes and functions in `Rio` along with their
    documentation.

    ## Parameters

    `postprocess`: Whether to apply rio-specific postprocessing to the
    documentation.
    """
    # Use heuristics to find all objects which should likely be public
    for obj in _find_possibly_public_objects():
        # Parse the object's docs
        if inspect.isclass(obj):
            docs = imy.docstrings.ClassDocs.from_class(obj)

            if postprocess:
                if issubclass(obj, rio.Component):
                    postprocess_component_docs(docs)
                else:
                    postprocess_class_docs(docs)

        elif callable(obj):
            docs = imy.docstrings.FunctionDocs.from_function(obj)

            if postprocess:
                postprocess_function_docs(docs)

        else:
            raise ValueError(f"Unexpected object type: {obj}")

        # Make the final determination whether this object is public
        if not docs.metadata.public:
            continue

        # This object is public
        yield obj, docs  # type: ignore


def postprocess_function_docs(docs: imy.docstrings.FunctionDocs) -> None:
    # Nothing here yet. This function exists for compatibility. If we ever
    # decide to add function-specific post-processing, we can do it here without
    # having to change all scripts.
    pass


def postprocess_class_docs(docs: imy.docstrings.ClassDocs) -> None:
    """
    Perform Rio specific post-processing on the component, such as stripping out
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
        keep = True

        keep = keep and not attr.name.startswith("_")
        keep = keep and attr.type is not dataclasses.KW_ONLY

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
        is_inherited_protected_method = (
            docs.name != "Component"
            and func.name
            in (
                "build",
                "call_event_handler",
                "force_refresh",
            )
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


def postprocess_component_docs(docs: imy.docstrings.ClassDocs) -> None:
    # Apply the standard class post-processing
    postprocess_class_docs(docs)

    # Remove the `bind()` method inherited from `rio.Component`, because
    # that method is only useful in custom components
    for i, func in enumerate(docs.functions):
        if func.name == "bind":
            del docs.functions[i]
            break
