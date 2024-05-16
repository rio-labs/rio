"""
Contains documentation related tasks specific to the Rio project.
"""

import dataclasses
import functools
import inspect
import types
from typing import *  # type: ignore

import imy.docstrings
import introspection
import unicall

import rio

__all__ = [
    "mark_as_private",
    "mark_constructor_as_private",
    "get_docs_for",
    "get_documentation_fragment",
    "build_documentation_url",
    "find_documented_objects",
    "postprocess_function_docs",
    "postprocess_class_docs",
    "postprocess_component_docs",
]


Class = TypeVar("Class", bound=type)
ClassOrFunction = TypeVar("ClassOrFunction", bound=type | types.FunctionType)


def mark_as_private(obj: ClassOrFunction) -> ClassOrFunction:
    if obj.__doc__ is None:
        obj.__doc__ = "## Metadata"
    elif "## Metadata" not in obj.__doc__:
        obj.__doc__ += "\n## Metadata"

    obj.__doc__ += "\npublic: False"

    return obj


def mark_constructor_as_private(cls: Class) -> Class:
    try:
        constructor = vars(cls)["__init__"]
    except KeyError:

        def constructor(self, *args, **kwargs):
            super(cls, self).__init__(*args, **kwargs)  # type: ignore (wtf?)

        introspection.add_method_to_class(constructor, cls, "__init__")

    mark_as_private(constructor)  # type: ignore (wtf?)

    return cls


def _make_docs_for_rio_url():
    docs = imy.docstrings.ClassDocs.from_class(rio.URL)
    docs.attributes.clear()
    docs.functions.clear()
    docs.summary = "Alias for `yarl.URL`."
    docs.details = """
Since URLs are a commonly used data type, `rio` re-exports `yarl.URL` as
`rio.URL` for convenience. See the
[`yarl` documentation](https://yarl.aio-libs.org/en/stable/api/#yarl.URL) for 
details about this class.
""".strip()

    return docs


DOCS_OVERRIDES: dict[
    Any, imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs
] = {
    rio.URL: _make_docs_for_rio_url(),
}


@overload
def get_docs_for(obj: type) -> imy.docstrings.ClassDocs: ...


@overload
def get_docs_for(obj: types.FunctionType) -> imy.docstrings.FunctionDocs: ...


@functools.lru_cache(maxsize=None)
def get_docs_for(
    obj: Callable | Type,
) -> imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs:
    """
    Parse the docs for a component and return them. The results are cached, so
    this function is fast.
    """

    try:
        return DOCS_OVERRIDES[obj]
    except KeyError:
        pass

    # Components and other classes
    if inspect.isclass(obj):
        docs = imy.docstrings.ClassDocs.from_class(obj)

        # Apply rio-specific post-processing
        if issubclass(obj, rio.Component):
            postprocess_component_docs(docs)
        else:
            postprocess_class_docs(docs)

        return docs

    # Functions
    if callable(obj):
        docs = imy.docstrings.FunctionDocs.from_function(obj)

        # Apply rio-specific post-processing
        postprocess_function_docs(docs)

        return docs

    # No clue
    raise ValueError(f"Cannot get docs for object `{obj}`")


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
        docs = get_docs_for(obj)

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

    # Strip out anything `Session` inherits from `unicall`
    if docs.name == "Session":
        to_remove = set(dir(unicall.Unicall)).difference(vars(rio.Session))
        docs.functions = [
            func for func in docs.functions if func.name not in to_remove
        ]

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
        if is_inherited_protected_method:
            keep = False

        # Strip lambdas
        if func.name == "<lambda>":
            keep = False

        # Make sure to keep the constructor
        if func.name == "__init__":
            keep = True

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

        # Check if it's explicitly excluded
        if not func.metadata.public:
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


def postprocess_component_docs(docs: imy.docstrings.ClassDocs) -> None:
    # Apply the standard class post-processing
    postprocess_class_docs(docs)

    # Remove the `bind()` method inherited from `rio.Component`, because
    # that method is only useful in custom components
    for i, func in enumerate(docs.functions):
        if func.name == "bind":
            del docs.functions[i]
            break
