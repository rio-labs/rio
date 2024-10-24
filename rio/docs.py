"""
Contains documentation related tasks specific to the Rio project.
"""

import dataclasses
import functools
import inspect
import re
import types
import typing as t

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
    "insert_links_into_markdown",
]


Class = t.TypeVar("Class", bound=type)
ClassOrFunction = t.TypeVar("ClassOrFunction", bound=type | types.FunctionType)


_NAME_TO_URL: dict[str, str] | None = None
_CODE_BLOCK_REGEX = re.compile(r"(.*?)(```.*?```|$)", flags=re.S)
_AUTO_LINK_REGEX = re.compile(r"`(?:rio\.)?([a-zA-Z_.]+)`(?!\])")


def insert_links_into_markdown(
    markdown: str, *, own_name: str | None = None
) -> str:
    """
    Turns markdown like

        `Row`

    into a link like

        [`Row`](/docs/api/row)

    The `own_name` parameter can be used to prevent a page from linking to
    itself. For example, in the documentation for `Row`, we don't want every
    occurrence of `Row` to turn into a link.
    """
    global _NAME_TO_URL

    if _NAME_TO_URL is None:
        _NAME_TO_URL = {}

        for docs in _get_unprocessed_docs().values():
            url = str(build_documentation_url(docs.name))
            _NAME_TO_URL[docs.name] = url

            # TODO: Also link methods and attributes (and parameters?) once they
            # have #url-fragments

    name_to_url = _NAME_TO_URL  # Reassign to appease the static type checker

    def repl(match: re.Match) -> str:
        name = match.group(1)

        if name != own_name:
            try:
                url = name_to_url[name]
            except KeyError:
                pass
            else:
                return f"[{match.group()}]({url})"

        return match.group()

    # We want to look for single-line text like `Row` and turn it into a link.
    # The problem is that such text might be appear inside of a code block (in a
    # comment). So we'll search for code blocks, and only apply the
    # substituation in the text before the code block.
    chunks = list[str]()

    for match_ in _CODE_BLOCK_REGEX.finditer(markdown):
        text, code_block = match_.groups()

        chunks.append(_AUTO_LINK_REGEX.sub(repl, text))
        chunks.append(code_block)

    return "".join(chunks)


def mark_as_private(obj: ClassOrFunction) -> ClassOrFunction:
    if obj.__doc__ is None:
        obj.__doc__ = "## Metadata"
    elif "## Metadata" not in obj.__doc__:
        obj.__doc__ += "\n## Metadata"

    obj.__doc__ += "\n`public`: False"

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


@t.overload
def get_docs_for(obj: type) -> imy.docstrings.ClassDocs: ...


@t.overload
def get_docs_for(obj: types.FunctionType) -> imy.docstrings.FunctionDocs: ...


def get_docs_for(
    obj: t.Callable | t.Type,
) -> imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs:
    """
    Parse the docs for a component and return them. The results are cached, so
    this function is fast.
    """
    return find_documented_objects()[obj]


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


def _find_possibly_public_objects() -> t.Iterable[t.Type | t.Callable]:
    """
    Finds all objects in rio that might be public. This uses heuristics to
    filter out many internal objects, but it's not perfect.
    """
    # Hardcoded items
    yield rio.App
    yield rio.AssetError
    yield rio.Color
    yield rio.ComponentPage
    yield rio.CursorStyle
    yield rio.escape_markdown
    yield rio.escape_markdown_code
    yield rio.FileInfo
    yield rio.Font
    yield rio.NavigationFailed
    yield rio.page
    yield rio.Redirect
    yield rio.Session
    yield rio.TextStyle
    yield rio.Theme
    yield rio.UserSettings
    yield rio.DateChangeEvent

    for module in (rio.event, rio.fills):
        for name in module.__all__:
            yield getattr(module, name)

    # Yield all events. There is no perfectly safe way to detect these
    # automatically, but the name is a good hint.
    for name, obj in vars(rio).items():
        if not name.endswith("Event"):
            continue

        assert inspect.isclass(obj), obj
        yield obj

    # Yield classes that also need their children documented
    to_do = [rio.Component]

    while to_do:
        cur = to_do.pop()

        # Skip anything not in the `rio` module
        if not cur.__module__.startswith("rio."):
            continue

        # Queue the children
        to_do.extend(cur.__subclasses__())

        # Hardcoded items that DON'T need documentation
        if cur.__name__ in (
            # Built-in components
            "ClassContainer",
            "DialogContainer",
            "FundamentalComponent",
            # Components from examples
            "NavButton",
            "DefaultRootComponent",
        ):
            continue

        # Internal
        if cur.__name__.startswith("_"):
            continue

        yield cur


@functools.cache
def _get_unprocessed_docs() -> (
    t.Mapping[
        type | t.Callable,
        imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs,
    ]
):
    """
    Finds all documented objects and parses their docstrings, but doesn't
    post-process them. This is necessary because post-processing involves
    inserting links to other documented objects, which requires a full list of
    documented objects. So post-processing has to be done later in a separate
    step.
    """

    result: dict = {
        rio.URL: _make_docs_for_rio_url(),
    }

    # Use heuristics to find all objects which should likely be public
    for obj in _find_possibly_public_objects():
        # Parse the object's docs
        if isinstance(obj, type):
            docs = imy.docstrings.ClassDocs.from_class(obj)
        else:
            docs = imy.docstrings.FunctionDocs.from_function(obj)

        # Make the final determination whether this object is public
        if not docs.metadata.public:
            continue

        # Make the summary into a single line. (This is because the summary is
        # sometimes displayed inside a `rio.Text`, which honors newlines. We
        # don't want that.)
        if docs.summary:
            docs.summary = docs.summary.replace("\n", " ")

        # This object is public
        result[obj] = docs

    return result


@functools.cache
def find_documented_objects() -> (
    t.Mapping[
        type | t.Callable,
        imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs,
    ]
):
    """
    Find all public classes and functions in `Rio` along with their
    documentation.
    """
    result = _get_unprocessed_docs()

    for docs in result.values():
        postprocess_docs(docs)

    return result


def postprocess_docs(
    docs: imy.docstrings.FunctionDocs | imy.docstrings.ClassDocs,
) -> None:
    """
    Applies rio-specific post-processing.
    """

    if isinstance(docs, imy.docstrings.FunctionDocs):
        postprocess_function_docs(docs)
    elif issubclass(docs.object, rio.Component):
        postprocess_component_docs(docs)
    else:
        postprocess_class_docs(docs)


def postprocess_function_docs(docs: imy.docstrings.FunctionDocs) -> None:
    if docs.summary is not None:
        docs.summary = insert_links_into_markdown(
            docs.summary, own_name=docs.name
        )

    if docs.details is not None:
        docs.details = insert_links_into_markdown(
            docs.details, own_name=docs.name
        )

    # Post-process the parameters
    for param_docs in docs.parameters:
        if param_docs.description:
            param_docs.description = insert_links_into_markdown(
                param_docs.description,
                own_name=f"{docs.name}.{param_docs.name}",
            )


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

    # Inserts links to other documentation
    if docs.summary is not None:
        docs.summary = insert_links_into_markdown(
            docs.summary, own_name=docs.name
        )

    if docs.details is not None:
        docs.details = insert_links_into_markdown(
            docs.details, own_name=docs.name
        )

    # Strip internal attributes
    index = 0
    while index < len(docs.attributes):
        prop = docs.attributes[index]

        # Decide whether to keep it
        keep = True

        keep = keep and not prop.name.startswith("_")
        keep = keep and prop.type is not dataclasses.KW_ONLY

        # Strip it out, if necessary
        if keep:
            index += 1
        else:
            del docs.attributes[index]

    # Additional per-attribute post-processing
    for prop in docs.attributes:
        # Insert links to other documentation pages
        if prop.description is not None:
            prop.description = insert_links_into_markdown(
                prop.description, own_name=f"{docs.name}.{prop.name}"
            )

    # Strip internal properties
    index = 0
    while index < len(docs.properties):
        prop = docs.properties[index]

        # Decide whether to keep it
        keep = not prop.name.startswith("_")

        # Strip it out, if necessary
        if keep:
            index += 1
        else:
            del docs.properties[index]

    # Additional per-property post-processing
    for prop in docs.properties:
        # Insert links to other documentation pages
        for func in (prop.getter, prop.setter):
            if func is None:
                continue

            if func.summary is not None:
                func.summary = insert_links_into_markdown(
                    func.summary, own_name=f"{docs.name}.{prop.name}"
                )

            if func.details is not None:
                func.details = insert_links_into_markdown(
                    func.details, own_name=f"{docs.name}.{prop.name}"
                )

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

        # Insert links to other documentation pages
        if func_docs.summary is not None:
            func_docs.summary = insert_links_into_markdown(
                func_docs.summary, own_name=f"{docs.name}.{func_docs.name}"
            )

        if func_docs.details is not None:
            func_docs.details = insert_links_into_markdown(
                func_docs.details, own_name=f"{docs.name}.{func_docs.name}"
            )

        # Post-process the parameters
        for param_docs in func_docs.parameters:
            if param_docs.description:
                param_docs.description = insert_links_into_markdown(
                    param_docs.description,
                    own_name=f"{docs.name}.{func_docs.name}.{param_docs.name}",
                )


def postprocess_component_docs(docs: imy.docstrings.ClassDocs) -> None:
    # Apply the standard class post-processing
    postprocess_class_docs(docs)

    # Remove the `bind()` method inherited from `rio.Component`, because
    # that method is only useful in custom components
    for i, func in enumerate(docs.functions):
        if func.name == "bind":
            del docs.functions[i]
            break

    # Subclasses of `rio.Component` inherit a load of constructor parameters,
    # which clutter the docs. We'll sort the keyword-only parameters so that the
    # inherited parameters appear at the end.
    if docs.object is not rio.Component:
        try:
            init_func = next(
                func for func in docs.functions if func.name == "__init__"
            )
        except StopIteration:
            pass
        else:
            parameters = list[imy.docstrings.FunctionParameter]()
            kwargs = list[imy.docstrings.FunctionParameter]()

            for param in init_func.parameters:
                if param.kw_only:
                    kwargs.append(param)
                else:
                    parameters.append(param)

            COMPONENT_CONSTRUCTOR_PARAMS = set(rio.Component.__annotations__)
            kwargs.sort(
                key=lambda param: param.name in COMPONENT_CONSTRUCTOR_PARAMS
            )
            parameters += kwargs

            init_func.parameters = parameters
