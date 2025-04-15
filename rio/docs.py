"""
Contains documentation related tasks specific to the Rio project.
"""

import collections
import functools
import inspect
import types
import typing as t

import imy.docstrings
import unicall

import rio

__all__ = [
    "get_rio_module_docs",
    "get_all_documented_objects",
    "get_toplevel_documented_objects",
    "get_docs_for",
    "get_documentation_url",
    "get_documentation_url_segment",
    "insert_links_into_markdown",
]


RIO_MODULE_DOCS: imy.docstrings.ModuleDocs | None = None
NAME_TO_DOCS: (
    t.Mapping[
        str,
        t.Sequence[
            imy.docstrings.ClassDocs
            | imy.docstrings.FunctionDocs
            | imy.docstrings.AttributeDocs
            | imy.docstrings.PropertyDocs
            | imy.docstrings.ParameterDocs,
        ],
    ]
    | None
) = None


def _prepare_docs():
    """
    Creates the `imy.docstrings.ModuleDocs` object for the `rio` module. This
    involves some expensive operations, so some useful data structures are
    cached in the global scope.
    """
    global RIO_MODULE_DOCS

    # Let imy parse the module
    RIO_MODULE_DOCS = imy.docstrings.ModuleDocs.from_module(rio)

    # Add stuff that imy doesn't consider public
    RIO_MODULE_DOCS.add_member(rio.event)
    RIO_MODULE_DOCS.add_member(rio.extension_event)

    url_docs = _make_docs_for_rio_url()
    url_docs.owner = RIO_MODULE_DOCS
    RIO_MODULE_DOCS.members["URL"] = url_docs

    # There's some trickery in the `Theme` for static typing purposes, which
    # involves some classes that we don't really want users to know about. Fix
    # up the affected docs.
    theme_docs = t.cast(
        imy.docstrings.ClassDocs, RIO_MODULE_DOCS.members["Theme"]
    )
    for attr in (
        "heading1_style",
        "heading2_style",
        "heading3_style",
        "text_style",
    ):
        # Ideally we would delete the PropertyDocs and replace them with
        # AttributeDocs, but I'd rather not have to instantiate one of imy's
        # classes here. They have a lot of parameters, and are quite likely to
        # change in the future.
        property_docs = t.cast(
            imy.docstrings.PropertyDocs, theme_docs.members[attr]
        )
        property_docs.getter.return_type = rio.TextStyle

    # Apply rio-specific post-processing
    postprocess_docs(RIO_MODULE_DOCS)

    # Insert links to other documentation pages
    _insert_hyperlinks_into_rio_docs(RIO_MODULE_DOCS)


def _insert_hyperlinks_into_rio_docs(
    rio_module_docs: imy.docstrings.ModuleDocs,
) -> None:
    # Make a list of all Docs objects we have to process
    all_docs = list(
        docs
        for docs in rio_module_docs.iter_children(
            include_self=True, recursive=True
        )
        # Exclude the getters and setters of properties. We only need the
        # properties themselves.
        if not (isinstance(docs.owner, imy.docstrings.PropertyDocs))
    )

    # Make a mapping from names to Docs objects. A name can refer to multiple
    # objects, e.g. `Rectangle` and `Card` both have a `content` attribute.
    name_to_docs = collections.defaultdict(list)

    for docs in all_docs:
        if isinstance(docs, imy.docstrings.ModuleDocs):
            continue

        names = [docs.name]
        if isinstance(
            docs, (imy.docstrings.ClassDocs, imy.docstrings.FunctionDocs)
        ):
            full_name = docs.full_name
            names += [full_name, full_name.removeprefix("rio.")]

        for name in names:
            name_to_docs[name].append(docs)

    # Cache the mapping, `insert_links_into_markdown` needs it
    global NAME_TO_DOCS
    NAME_TO_DOCS = name_to_docs

    # Loop over all the docs objects and insert hyperlinks into their markdown
    for docs in all_docs:
        # Not everything needs to be hyperlinked. A page doesn't need to link to
        # itself. A parameter doesn't need to link to its function. Etc.
        urls_to_ignore = _get_urls_to_ignore(docs)

        docs.transform_docstrings(
            lambda markdown: insert_links_into_markdown(
                markdown,
                urls_to_ignore=urls_to_ignore,
            )
        )


def _get_urls_to_ignore(docs) -> t.Sequence[rio.URL]:
    if isinstance(docs, imy.docstrings.ModuleDocs):
        return ()

    urls_to_ignore = [url_for_docs(docs)]

    # Class members don't need to link their class
    if isinstance(
        docs, (imy.docstrings.PropertyDocs, imy.docstrings.AttributeDocs)
    ):
        urls_to_ignore += _get_urls_to_ignore(docs.owner)
    elif isinstance(docs, imy.docstrings.FunctionDocs):
        if isinstance(docs.owner, imy.docstrings.ClassDocs):
            urls_to_ignore += _get_urls_to_ignore(docs.owner)
    # Parameters don't need to link to the function
    elif isinstance(docs, imy.docstrings.ParameterDocs):
        urls_to_ignore += _get_urls_to_ignore(docs.owner)

    return urls_to_ignore


def get_rio_module_docs() -> imy.docstrings.ModuleDocs:
    """
    Returns the `imy.docstrings.ModuleDocs` object for the `rio` module.
    """
    if RIO_MODULE_DOCS is None:
        _prepare_docs()
        assert RIO_MODULE_DOCS is not None

    return RIO_MODULE_DOCS


@functools.cache
def get_all_documented_objects() -> dict[
    type | t.Callable | property,
    imy.docstrings.ClassDocs
    | imy.docstrings.FunctionDocs
    | imy.docstrings.PropertyDocs,
]:
    all_docs = get_rio_module_docs().iter_children(
        include_self=True, recursive=True
    )
    return {
        docs.object: docs
        for docs in all_docs
        if isinstance(
            docs,
            (
                imy.docstrings.ClassDocs,
                imy.docstrings.FunctionDocs,
                imy.docstrings.PropertyDocs,
            ),
        )
    }


@functools.cache
def get_toplevel_documented_objects() -> dict[
    type | t.Callable,
    imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs,
]:
    """
    Returns only objects that have their own page in our docs. (That means no
    methods.)
    """
    return {
        docs.object: docs
        for docs in get_all_documented_objects().values()
        if isinstance(
            docs, (imy.docstrings.ClassDocs, imy.docstrings.FunctionDocs)
        )
        and isinstance(docs.owner, imy.docstrings.ModuleDocs)
    }


@t.overload
def get_docs_for(obj: type) -> imy.docstrings.ClassDocs: ...


@t.overload
def get_docs_for(obj: types.FunctionType) -> imy.docstrings.FunctionDocs: ...


def get_docs_for(
    obj: types.FunctionType | t.Type,
) -> imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs:
    """
    Parse the docs for a component and return them. The results are cached, so
    this function is fast.
    """
    return get_all_documented_objects()[obj]  # type: ignore


def _make_docs_for_rio_url():
    docs = imy.docstrings.ClassDocs.from_class(rio.URL)
    docs.attributes.clear()
    docs.members.clear()
    docs.summary = "Alias for `yarl.URL`."
    docs.details = """
Since URLs are a commonly used data type, Rio re-exports `yarl.URL` as
`rio.URL` for convenience. See the
[`yarl` documentation](https://yarl.aio-libs.org/en/stable/api/#yarl.URL) for
details about this class.
""".strip()

    return docs


def get_documentation_url(
    obj: type | t.Callable,
    *,
    relative: bool = False,
) -> rio.URL:
    """
    Returns the URL to the documentation for the given Rio object. This doesn't
    perform any checks on whether the object actually exists and has
    documentation. It relies solely on the passed values.

    (This function is used by the dev tools.)
    """
    # Build the relative URL
    url = f"/docs/api/{get_documentation_url_segment(obj)}"

    # Make it absolute, if requested
    if not relative:
        url = "https://rio.dev" + url

    # Done
    return rio.URL(url)


def get_documentation_url_segment(obj: type | t.Callable) -> str:
    """
    Returns the URL segment for the documentation of the given Rio object. This
    doesn't perform any checks on whether the object actually exists and has
    documentation. It relies solely on the passed in values.

    (This function is used by the rio website to generate pages.)
    """
    return obj.__name__.lower()


def url_for_docs(
    docs: imy.docstrings.ClassDocs
    | imy.docstrings.FunctionDocs
    | imy.docstrings.AttributeDocs
    | imy.docstrings.PropertyDocs
    | imy.docstrings.ParameterDocs,
    *,
    relative: bool = False,
) -> rio.URL:
    # Classes and functions (not methods!) have their own documentation page, so
    # those simply defer to `get_documentation_url`.
    if isinstance(docs, imy.docstrings.ClassDocs):
        return get_documentation_url(docs.object, relative=relative)

    if isinstance(docs, imy.docstrings.FunctionDocs):
        # Methods are listed on the page of the class, so get the url for the
        # class and then add the function name
        if isinstance(docs.owner, imy.docstrings.ClassDocs):
            url = url_for_docs(docs.owner, relative=relative)
            # ScrollTargets currently don't work, so don't create urls with
            # #fragments
            return url  # + f"#{docs.name.lower()}"
        else:
            return get_documentation_url(docs.object)

    # ScrollTargets currently don't work, so don't create urls with #fragments
    """
    # Fields and properties are listed on the page of the class, so get the url
    # for the class and then add an url fragment
    if isinstance(docs, (imy.docstrings.AttributeDocs, imy.docstrings.PropertyDocs)):
        url = url_for_docs(docs.owner, relative=relative)
        return url + f"#{docs.name.lower()}"

    # Parameters are listed on the page of the function, so get the url for the
    # function and then add an url fragment
    if isinstance(docs, imy.docstrings.ParameterDocs):
        url = url_for_docs(docs.owner, relative=relative)

        if "#" in url:
            return url + f".{docs.name.lower()}"
        else:
            return url + f"#{docs.name.lower()}"
    """
    assert docs.owner is not None
    return url_for_docs(docs.owner)

    assert False, f"url_for_docs received invalid input: {docs}"


def postprocess_docs(
    docs: imy.docstrings.FunctionDocs
    | imy.docstrings.ClassDocs
    | imy.docstrings.ModuleDocs,
) -> None:
    """
    Applies rio-specific post-processing.
    """

    # Make the summary into a single line. (This is because the summary is
    # sometimes displayed inside a `rio.Text`, which honors newlines. We
    # don't want that.)
    if docs.summary:
        docs.summary = docs.summary.replace("\n", " ")

    if isinstance(docs, imy.docstrings.ModuleDocs):
        postprocess_module_docs(docs)
    elif isinstance(docs, imy.docstrings.FunctionDocs):
        postprocess_function_docs(docs)
    elif issubclass(docs.object, rio.Component):
        postprocess_component_docs(docs)
    else:
        postprocess_class_docs(docs)


def postprocess_module_docs(docs: imy.docstrings.ModuleDocs) -> None:
    for member in docs.members.values():
        postprocess_docs(member)


def postprocess_function_docs(docs: imy.docstrings.FunctionDocs) -> None:
    pass


def postprocess_class_docs(docs: imy.docstrings.ClassDocs) -> None:
    """
    Perform Rio specific post-processing on the component, such as stripping out
    internal attributes and functions.
    """

    # Strip out anything `Session` inherits from `unicall`
    if docs.name == "Session":
        to_remove = set(dir(unicall.Unicall)).difference(vars(rio.Session))
        docs.members = {
            name: member
            for name, member in docs.members.items()
            if name not in to_remove
        }

    # Strip default docstrings created by dataclasses
    if docs.summary is not None and docs.summary.startswith(f"{docs.name}("):
        docs.summary = None
        docs.details = None

    # Skip internal functions
    def keep_method(func: imy.docstrings.FunctionDocs) -> bool:
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
        if func.name == "__init__":
            if (
                docs.name in ("FileInfo", "Session")
                or docs.name.endswith(("Event", "Error"))
                or inspect.isabstract(docs.object)
            ):
                keep = False

        # Check if it's explicitly excluded
        if not func.metadata.public:
            keep = False

        return keep

    docs.members = {
        name: member
        for name, member in docs.members.items()
        if not isinstance(member, imy.docstrings.FunctionDocs)
        or keep_method(member)
    }

    # Post-process the constructor
    try:
        init_function = docs.members["__init__"]
    except KeyError:
        pass
    else:
        assert isinstance(init_function, imy.docstrings.FunctionDocs)

        # Strip the ridiculous default docstring created by dataclasses
        #
        # FIXME: Not working for some reason
        if (
            init_function.summary
            == "Initialize self. See help(type(self)) for accurate signature."
        ):
            init_function.summary = None
            init_function.details = None

        # Inject a short description for `__init__` if there is none.
        if init_function.summary is None:
            init_function.summary = f"Creates a new `{docs.name}` instance."


def postprocess_component_docs(docs: imy.docstrings.ClassDocs) -> None:
    # Apply the standard class post-processing
    postprocess_class_docs(docs)

    if docs.object is not rio.Component:
        # Remove methods that are only useful in custom components
        docs.members = {
            name: member
            for name, member in docs.members.items()
            if name
            not in ("bind", "build", "call_event_handler", "force_refresh")
        }

        # Subclasses of `rio.Component` inherit a load of constructor
        # parameters, which clutter the docs. We'll sort the keyword-only
        # parameters so that the inherited parameters appear at the end.
        try:
            init_func = docs.members["__init__"]
        except KeyError:
            pass
        else:
            assert isinstance(init_func, imy.docstrings.FunctionDocs)

            parameters = list[imy.docstrings.ParameterDocs]()
            kwargs = list[imy.docstrings.ParameterDocs]()

            for param in init_func.parameters.values():
                if param.kw_only:
                    kwargs.append(param)
                else:
                    parameters.append(param)

            COMPONENT_CONSTRUCTOR_PARAMS = set(rio.Component.__annotations__)
            kwargs.sort(
                key=lambda param: param.name in COMPONENT_CONSTRUCTOR_PARAMS
            )
            parameters += kwargs

            init_func.parameters = {param.name: param for param in parameters}


def insert_links_into_markdown(
    markdown: str,
    *,
    urls_to_ignore: t.Iterable[rio.URL] = (),
) -> str:
    if NAME_TO_DOCS is None:
        _prepare_docs()
        assert NAME_TO_DOCS is not None

    name_to_docs = NAME_TO_DOCS  # Reassign to appease the type checker

    urls_to_ignore_as_str = {str(url) for url in urls_to_ignore}

    def url_for_name(name: str) -> str | None:
        possible_targets = {
            str(url_for_docs(docs)) for docs in name_to_docs.get(name, ())
        }

        # Filter out ignored urls
        possible_targets.difference_update(urls_to_ignore_as_str)

        if not possible_targets:
            return None

        if len(possible_targets) == 1:
            return possible_targets.pop()

        # TODO: Can we somehow figure out which url was meant?
        return None

    return imy.docstrings.insert_links_into_markdown(
        markdown,
        url_for_name=url_for_name,
    )
