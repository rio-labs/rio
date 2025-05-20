from __future__ import annotations

import abc
import dataclasses
import functools
import logging
import typing as t
import warnings
from pathlib import Path

import imy.docstrings
import introspection.typing
import path_imports
from introspection import convert_case

import rio.components.error_placeholder

from . import deprecations, url_pattern, utils
from .errors import NavigationFailed

__all__ = [
    "Redirect",
    "ComponentPage",
    "page",
    "GuardEvent",
    "QueryParameter",
]


DEFAULT_ICON = "rio/logo:color"


class QUERY_PARAMETER:
    pass


T = t.TypeVar("T")
QueryParameter = t.Annotated[T, QUERY_PARAMETER]


@t.final
@dataclasses.dataclass(frozen=True)
class Redirect:
    """
    Redirects the user to a different page.

    Redirects can be added to the app in place of "real" pages. These are
    useful for cases where you want to add valid links to the app, but don't
    want to display a page at that URL. They redirect users to another page
    the instant they would be opened.

    Redirects are passed directly to the app during construction, like so:

    ```python
    import rio

    app = rio.App(
        build=lambda: rio.Column(
            rio.Text("Welcome to my app!"),
            rio.PageView(grow_y=True),
        ),
        pages=[
            rio.ComponentPage(
                name="Home",
                url_segment="",
                build=lambda: rio.Text("This is the home page"),
            ),
            rio.ComponentPage(
                name="Subpage",
                url_segment="subpage",
                build=lambda: rio.Text("This is a subpage"),
            ),
            rio.Redirect(
                url_segment="old-page",
                target="/subpage",
            ),
        ],
    )

    app.run_in_browser()
    ```

    ## Attributes

    `url_segment`: The URL segment at which this page should be displayed. For
        example, if this is "subpage", then the page will be displayed at
        "https://yourapp.com/subpage". If this is "", then the page will be
        displayed at the root URL.

    `target`: The URL to which the user should be redirected.
    """

    url_segment: str
    target: str | rio.URL

    # A pre-parsed URL pattern object, used to verify whether a URL matches
    # this page, as well as extracting path parameters
    _url_pattern: url_pattern.UrlPattern = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        vars(self).update(
            # Verify and parse the URL
            _url_pattern=url_pattern.UrlPattern(self.url_segment),
        )


@t.final
@deprecations.parameter_renamed(
    since="0.10",
    old_name="page_url",
    new_name="url_segment",
)
@dataclasses.dataclass(frozen=True)
class ComponentPage:
    """
    A routable page in a Rio app.

    Rio apps can consist of many pages. You might have a welcome page, a
    settings page, a login, and so on. `ComponentPage` components contain all
    information needed to display those pages, as well as to navigate between
    them.

    This is not just specific to websites. Apps might, for example, have
    a settings page, a profile page, a help page, and so on.

    Pages are passed directly to the app during construction, like so:

    ```python
    import rio

    app = rio.App(
        build=lambda: rio.Column(
            rio.Text("Welcome to my app!"),
            rio.PageView(grow_y=True),
        ),
        pages=[
            rio.ComponentPage(
                name="Home",
                url_segment="",
                build=lambda: rio.Text("This is the home page"),
            ),
            rio.ComponentPage(
                name="Subpage",
                url_segment="subpage",
                build=lambda: rio.Text("This is a subpage"),
            ),
        ],
    )
    ```

    This will display "This is the home page" when navigating to the root URL,
    but "This is a subpage" when navigating to "/subpage". Note that on both
    pages the text "Welcome to my page!" is displayed above the page content.
    That's because it's not part of the `PageView`.

    For additional details, please refer to [Multiple
    Pages](https://rio.dev/docs/howto/multiple-pages) and [Route
    Parameters](https://rio.dev/docs/howto/route-parameters).

    ## Attributes

    `name`: A human-readable name for the page. While the page itself doesn't
        use this value directly, it serves as important information for
        debugging, as well as other components such as navigation bars.

    `url_segment`: The URL segment at which this page should be displayed. For
        example, if this is "subpage", then the page will be displayed at
        "https://yourapp.com/subpage". If this is "", then the page will be
        displayed at the root URL.

    `build`: A callback that is called when this page is displayed. It should
        return a Rio component.

    `icon`: The name of an icon to associate with the page. While the page
        itself doesn't use this value directly, it serves as additional
        information for other components such as navigation bars.

    `children`: A list of child pages. These pages will be displayed when
        navigating to a sub-URL of this page. For example, if this page's
        `url_segment` is "page1", and it has a child page with `url_segment`
        "page2", then the child page will be displayed at
        "https://yourapp.com/page1/page2".

    `meta_tags`: A dictionary of meta tags to include in the page's HTML. These
        are used by search engines and social media sites to display
        information about your page.

    `guard`: A callback that is called before this page is displayed. It
        can prevent users from accessing pages which they are not allowed to
        see. For example, you may want to redirect users to your login page
        if they are trying to access their profile page without being
        logged in.

        The callback should return `None` if the user is allowed to access
        the page, or a string or `rio.URL` if the user should be redirected
        to a different page.
    """

    name: str
    url_segment: str
    build: t.Callable[..., rio.Component]
    _: dataclasses.KW_ONLY
    icon: str = DEFAULT_ICON
    children: t.Sequence[ComponentPage | Redirect] = dataclasses.field(
        default_factory=list
    )
    guard: t.Callable[[rio.GuardEvent], None | rio.URL | str] | None = None
    meta_tags: dict[str, str] = dataclasses.field(default_factory=dict)

    # This is used to allow users to order pages when using the `rio.page`
    # decorator. It's not public, but simply a convenient place to store this.
    _page_order_: int | None = dataclasses.field(default=None, init=False)

    # A pre-parsed URL pattern object, used to verify whether a URL matches
    # this page, as well as extracting path parameters
    _url_pattern: url_pattern.UrlPattern = dataclasses.field(init=False)

    # The names of the query parameters that are passed to the `build` function
    _url_parameter_parsers: t.Mapping[str, UrlParameterParser] = (
        dataclasses.field(init=False)
    )

    def __post_init__(self) -> None:
        # Verify and parse the URL
        vars(self)["_url_pattern"] = url_pattern.UrlPattern(self.url_segment)

        # Verify the `build` function and prepare the parsers for the URL
        # parameters
        try:
            vars(self)["_url_parameter_parsers"] = (
                self._verify_build_function_and_get_parameter_parsers()
            )
        except TypeError as error:
            raise TypeError(
                f"{self.build} is not a valid `build` function: {error}"
            ) from None

    def _verify_build_function_and_get_parameter_parsers(
        self,
    ) -> t.Mapping[str, UrlParameterParser]:
        # Figure out which query parameters we need to pass to the `build`
        # function and how to parse them
        signature = introspection.signature(self.build)
        url_parameter_parsers = {}

        for param_name, parameter in signature.parameters.items():
            # Is this a path parameter, a query parameter, or neither?
            try:
                type_info = introspection.typing.TypeInfo(
                    parameter.annotation,
                    forward_ref_context=parameter.forward_ref_context,
                )
            except introspection.errors.CannotResolveForwardref:
                # If it seems likely that this was supposed to be a query
                # parameter, emit a warning. Otherwise, silently ignore it.
                if isinstance(parameter.annotation, t.ForwardRef):
                    annotation_str = parameter.annotation.__forward_arg__
                else:
                    annotation_str = str(parameter.annotation)

                annotation_str = annotation_str.lower()

                if "query" in annotation_str or "param" in annotation_str:
                    warnings.warn(
                        f"The type annotation of the {param_name!r} parameter"
                        f" of the {self.build.__name__!r} `build` function"
                        f" cannot be resolved. If this was intended to be a"
                        f" query parameter, make sure the annotation is valid"
                        f" at runtime."
                    )

                continue

            if param_name not in self._url_pattern.path_parameter_names:
                if QUERY_PARAMETER not in type_info.annotations:
                    continue

                # Query parameters must have default values
                if not parameter.is_optional:
                    raise TypeError(
                        f"The query parameter {param_name!r} doesn't have a default value"
                    )

            if parameter.kind not in (
                introspection.Parameter.POSITIONAL_OR_KEYWORD,
                introspection.Parameter.KEYWORD_ONLY,
            ):
                raise TypeError(
                    f"The {param_name!r} parameter isn't a keyword parameter"
                )

            if parameter.annotation is introspection.Parameter.empty:
                raise TypeError(
                    f"The {param_name!r} parameter doesn't have a type annotation"
                )

            url_parameter_parsers[param_name] = _get_parser_for_annotation(
                type_info
            )

        # Make sure no parameters that were defined in the URL pattern are
        # missing
        for param_name in self._url_pattern.path_parameter_names:
            if param_name not in signature.parameters:
                raise TypeError(
                    f"{self.build} is not a valid `build` function: The URL pattern defines a parameter {param_name!r}, but the function doesn't have such a parameter"
                )

        return url_parameter_parsers

    def _safe_build_with_url_parameters(
        self,
        path_params: t.Mapping[str, object],
        raw_query_params: t.Mapping[str, str],
    ) -> rio.Component:
        parsed_query_params = self._parse_query_parameters(raw_query_params)
        return utils.safe_build(
            self.build, **path_params, **parsed_query_params
        )

    def _parse_query_parameters(
        self, query_params: t.Mapping[str, str]
    ) -> t.Mapping[str, object]:
        parsed_params = dict[str, object]()

        for name, raw_value in query_params.items():
            try:
                parser = self._url_parameter_parsers[name]
            except KeyError:
                continue

            try:
                parsed_params[name] = parser.parse(raw_value)
            except ValueError:
                pass

        return parsed_params


@deprecations.deprecated(since="0.10", replacement=ComponentPage)
@introspection.set_signature(ComponentPage)
def Page(*args, **kwargs):
    return ComponentPage(*args, **kwargs)


class UrlParameterParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, value: str) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def list_valid_values(self) -> t.Sequence[str]:
        """
        List all values that can be parsed by this parser, if there is a
        reasonable amount of them. (Don't list all floats, for example.) If
        there are too many, throw a `ValueError`.
        """
        raise NotImplementedError


class FuncParser(UrlParameterParser):
    """
    A simple parser that simply calls a function to parse the value.
    `list_valid_values()` always throws a `ValueError`.
    """

    def __init__(self, parse_function: t.Callable[[str], object]):
        self._parse = parse_function

    def parse(self, value: str) -> object:
        return self._parse(value)

    def list_valid_values(self):
        raise ValueError


class BooleanParser(UrlParameterParser):
    def parse(self, value: str) -> bool:
        value = value.lower()

        if value in ("true", "t", "yes", "y", "1"):
            return True

        if value in ("false", "f", "no", "n", "0"):
            return False

        raise ValueError(f"{value!r} cannot be parsed as a boolean")

    def list_valid_values(self):
        return ("true", "false")


class LiteralParser(UrlParameterParser):
    def __init__(self, values: tuple[object, ...]):
        self.values = values

        types = {type(value) for value in values}
        if len(types) > 1:
            raise TypeError(
                "`Literal`s with values of different types aren't supported"
            )

        parameter_type = types.pop()
        try:
            self._sub_parser = _get_parser_for_annotation(
                introspection.typing.TypeInfo(parameter_type)
            )
        except TypeError:
            raise TypeError(
                f"`Literal`s of type {parameter_type.__name__} aren't supported"
            ) from None

    def parse(self, value: str):
        parsed_value = self._sub_parser.parse(value)

        if parsed_value in self.values:
            return parsed_value

        raise ValueError(f"{value!r} doesn't match any of the allowed literals")

    def list_valid_values(self) -> t.Sequence[str]:
        return [str(value) for value in self.values]


def _get_parser_for_annotation(
    annotation: introspection.typing.TypeInfo,
) -> UrlParameterParser:
    TYPE_TO_PARSER_FUNC: t.Mapping[
        introspection.types.TypeAnnotation, t.Callable[[str], object]
    ] = {
        str: str,
        int: int,
        float: float,
    }

    try:
        parser_func = TYPE_TO_PARSER_FUNC[annotation.type]
    except KeyError:
        pass
    else:
        return FuncParser(parser_func)

    if annotation.type == bool:
        return BooleanParser()

    if annotation.type == t.Literal:
        assert annotation.arguments
        return LiteralParser(annotation.arguments)

    # As a special case, `None` is allowed in type annotations because it's a
    # popular default value, but we won't actually parse it. It can *only* be
    # used as a default value.
    if annotation.type == t.Optional:
        subtype: introspection.types.TypeAnnotation = annotation.arguments[0]  # type: ignore
        return _get_parser_for_annotation(
            introspection.typing.TypeInfo(
                subtype, forward_ref_context=annotation.forward_ref_context
            )
        )

    raise TypeError(
        f"Parameters of type {annotation.type} aren't supported"
    ) from None


def _get_active_page_instances(
    *,
    available_pages: t.Iterable[rio.ComponentPage | rio.Redirect],
    remaining_path: str,
) -> list[
    tuple[
        rio.ComponentPage | rio.Redirect,
        dict[str, object],
    ]
]:
    """
    Given a list of available pages, and a URL, return the list of pages that
    would be active if navigating to that URL. Each result entry contains the

    - Page (ComponentPage / Redirect) that would be active
    - The path arguments passed to that page

    The path is a string rather than URL, so matching can be done efficiently
    and the function can recurse on it. The path string must not start with a
    slash.
    """
    assert not remaining_path.startswith("/"), remaining_path

    # Get the first matching page
    for page in available_pages:
        did_match, raw_path_arguments, remainder = page._url_pattern.match(
            remaining_path
        )

        if not did_match:
            continue

        # Try parsing the path arguments
        if isinstance(page, rio.ComponentPage):
            try:
                path_arguments = {
                    name: page._url_parameter_parsers[name].parse(value)
                    for name, value in raw_path_arguments.items()
                }
            except ValueError:
                continue

        else:
            path_arguments = raw_path_arguments

        break

    # No matching page found
    else:
        return []

    # Remember this page
    path_arguments = t.cast(dict[str, object], path_arguments)
    active_pages = [
        (page, path_arguments),
    ]

    # Recurse into the children
    if isinstance(page, rio.ComponentPage):
        active_pages += _get_active_page_instances(
            available_pages=page.children,
            remaining_path=remainder,
        )

    return active_pages


@t.final
@imy.docstrings.mark_constructor_as_private
@dataclasses.dataclass(frozen=True)
class GuardEvent:
    """
    Holds information regarding a guard event.

    This is a simple dataclass that stores useful information for the guard
    event. They can prevent users from accessing pages which they are not
    allowed to see.

    ## Attributes

    `session`: The current session.

    `active_pages`: All pages that will be active if the navigation succeeds.
    """

    # The current session
    session: rio.Session

    # The pages that would be activated by this navigation
    #
    # This is an `Sequence` rather than `list`, because the same event instance
    # is reused for multiple event handlers. This allows to assign a tuple, thus
    # preventing modifications.
    active_pages: t.Sequence[ComponentPage | Redirect]


def check_page_guards(
    sess: rio.Session,
    target_url_absolute: rio.URL,
) -> tuple[
    tuple[
        tuple[ComponentPage, dict[str, object]],
        ...,
    ]
    | None,
    rio.URL,
]:
    """
    Check whether navigation to the given target URL is possible.

    This finds the pages that would be activated by this navigation and runs
    their guards. If the guards effect a redirect, it instead attempts to
    navigate to the redirect target, and so on.

    Raises `NavigationFailed` if navigation to the target URL is not possible
    because of an error, such as an exception in a guard.

    If the URL points to a page which doesn't exist that is not considered an
    error. The result will still be valid. That is because navigation is
    possible, it's just that some `PageView`s will display a 404 page.

    If attempting to navigate to a URL that isn't path of the app, i.e. it's not
    a child of the app's configured base URL, `None` is returned instead of
    active pages.

    This function does not perform any actual navigation. It simply checks
    whether navigation to the target page is possible.

    The result is a tuple of two elements:

    - A tuple of tuples, where each inner tuple contains a page that would be
      activated by the navigation, and the path arguments that would be passed
      to that page during building.

    - The URL that the navigation would actually lead to. This is the URL that
      the user would see in their browser's address bar after the navigation
      completes.
    """

    assert target_url_absolute.is_absolute(), target_url_absolute

    # Is any guard opposed to this page?
    initial_target_url = target_url_absolute
    visited_redirects = {target_url_absolute}
    past_redirects = [target_url_absolute]

    while True:
        # Strip the base. This also detects navigation to outside of the app
        try:
            target_url_relative = utils.url_relative_to_base(
                sess._base_url, target_url_absolute
            )
        except ValueError:
            return None, target_url_absolute

        # Find all pages which would by activated by this navigation
        active_page_instances_and_path_arguments = tuple(
            _get_active_page_instances(
                available_pages=sess.app.pages,
                remaining_path=target_url_relative.path,
            )
        )

        # Check the guards for each activated page
        active_page_instances = tuple(
            page for page, _ in active_page_instances_and_path_arguments
        )

        redirect = None
        event = GuardEvent(
            session=sess,
            active_pages=active_page_instances,
        )

        for page in active_page_instances:
            if isinstance(page, Redirect):
                redirect = page.target
            else:
                if page.guard is None:
                    continue

                try:
                    redirect = page.guard(event)
                except Exception as err:
                    message = f"Rejecting navigation to `{initial_target_url}` because of an error in a page guard of `{page.url_segment}`: {err}"
                    logging.exception(message)
                    raise NavigationFailed(message)

            if redirect is not None:
                break

        # All guards are satisfied - done
        if redirect is None:
            assert all(
                isinstance(page, rio.ComponentPage)
                for page in active_page_instances
            ), active_page_instances

            return (
                active_page_instances_and_path_arguments,  # type: ignore (there cannot be any Redirects here anymore)
                target_url_absolute,
            )

        # A guard wants to redirect to a different page
        redirect = apply_redirect(sess, target_url_absolute, redirect)
        assert redirect.is_absolute(), redirect

        # Detect infinite loops and break them
        if redirect in visited_redirects:
            page_strings = [
                str(url_segment) for url_segment in past_redirects + [redirect]
            ]
            page_strings_list = "\n -> ".join(page_strings)

            message = f"Rejecting navigation to `{initial_target_url}` because page guards have created an infinite loop:\n\n    {page_strings_list}"
            logging.warning(message)
            raise NavigationFailed(message)

        # Remember that this page has been visited before
        visited_redirects.add(redirect)
        past_redirects.append(redirect)

        # Rinse and repeat
        target_url_absolute = redirect


def apply_redirect(
    sess: rio.Session, active_url: rio.URL, target_url: rio.URL | str
) -> rio.URL:
    """
    Applies a redirect to the given URL. This effectively joins the two URLs
    while preserving the query parameters and URL fragments of the active URL
    (unless the redirect overwrites them).
    """
    # Use the usual `_make_url_absolute` function to ensure consistent behavior
    target_url_absolute = sess._make_url_absolute(
        target_url, active_page_url_override=active_url
    )

    # Set the fragment
    target_url_absolute = target_url_absolute.with_fragment(
        target_url_absolute.fragment or active_url.fragment
    )

    # Set the query parameters
    query_parameters = dict(active_url.query)
    query_parameters.update(target_url_absolute.query)
    target_url_absolute = target_url_absolute.with_query(query_parameters)

    return target_url_absolute


BuildFunction = t.Callable[..., "rio.Component"]
C = t.TypeVar("C", bound=BuildFunction)


BUILD_FUNCTION_TO_PAGE = dict[BuildFunction, ComponentPage]()


def page(
    *,
    url_segment: str | None = None,
    name: str | None = None,
    icon: str = DEFAULT_ICON,
    guard: t.Callable[[GuardEvent], None | rio.URL | str] | None = None,
    meta_tags: dict[str, str] | None = None,
    order: int | None = None,
) -> t.Callable[[C], C]:
    """
    This decorator creates a page (complete with URL, icon, etc) that displays
    the decorated component. All parameters are optional, and if omitted,
    sensible defaults will be inferred based on the name of the decorated class.

    In order to create a "root" page, set the `url_segment` to an empty string:

    ```py
    @rio.page(
        url_segment="",
    )
    class HomePage(rio.Component):
        def build(self):
            return rio.Text(
                "Welcome to my website",
                style="heading1",
            )
    ```

    For additional details, please refer to the how-to guide [Multiple
    Pages](https://rio.dev/docs/howto/multiple-pages).


    ## Parameters

    `url_segment`: The URL segment at which this page should be displayed. For
        example, if this is "subpage", then the page will be displayed at
        "https://yourapp.com/subpage". If this is "", then the page will be
        displayed at the root URL.

    `name`: A human-readable name for the page. While the page itself doesn't
        use this value directly, it serves as important information for
        debugging, as well as other components such as navigation bars.

    `icon`: The name of an icon to associate with the page. While the page
        itself doesn't use this value directly, it serves as additional
        information for other components such as navigation bars.

    `meta_tags`: A dictionary of meta tags to include in the page's HTML. These
        are used by search engines and social media sites to display
        information about your page.

    `guard`: A callback that is called before this page is displayed. It
        can prevent users from accessing pages which they are not allowed to
        see. For example, you may want to redirect users to your login page
        if they are trying to access their profile page without being
        logged in.

        The callback should return `None` if the user is allowed to access
        the page, or a string or `rio.URL` if the user should be redirected
        to a different page.

    `order`: An int that controls the order of this page relative to its
        siblings. Similar to the `name`, this is relevant for navigation bars.
    """

    def decorator(build: C) -> C:
        nonlocal name, url_segment

        # Derive a default name
        if name is None:
            name = (
                convert_case(build.__name__, "snake").replace("_", " ").title()
            )

        # Derive a default URL segment
        if url_segment is None:
            url_segment = convert_case(build.__name__, "kebab").lower()

        # Create the result
        page = ComponentPage(
            name=name,
            url_segment=url_segment,
            build=build,
            icon=icon,
            guard=guard,
            meta_tags=meta_tags or {},
        )

        # The component page has a field specifically so this decorator can
        # store the page order. However, since this is a frozen dataclass,
        # contortions are needed
        page.__dict__["_page_order_"] = order

        # Store the result
        BUILD_FUNCTION_TO_PAGE[build] = page

        # Return the original class
        return build

    return decorator


def _page_sort_key(page: rio.ComponentPage) -> tuple:
    """
    Returns a key that can be used to sort pages.
    """
    return (
        # Put the home page first
        not page.url_segment == "",
        # Then sort by name
        page.name,
    )


def auto_detect_pages(
    directory: Path,
    *,
    package: str | None = None,
) -> list[rio.ComponentPage]:
    # Find all pages using the iterator method
    pages = _auto_detect_pages_iter(directory, package=package)

    # Sort them, ignoring any user-specified ordering for now
    pages = sorted(pages, key=_page_sort_key)

    # Now apply the user-specified ordering. This sorting is stable, hence the
    # previous step.
    utils.soft_sort(pages, key=lambda page: page._page_order_)

    # Done
    return pages


def _auto_detect_pages_iter(
    directory: Path,
    *,
    package: str | None = None,
) -> t.Iterable[rio.ComponentPage]:
    try:
        contents = list(directory.iterdir())
    except FileNotFoundError:
        return

    for file_path in contents:
        if not utils.is_python_script(file_path):
            continue

        yield _page_from_python_file(file_path, package)


def _page_from_python_file(
    file_path: Path, package: str | None
) -> ComponentPage:
    module_name = file_path.stem
    if package is not None:
        module_name = package + "." + module_name

    try:
        module = path_imports.import_from_path(
            file_path,
            module_name=module_name,
            force_reimport=False,
        )
    except BaseException as error:
        import traceback

        traceback.print_exc()

        # Can't import the module? Display a warning and a placeholder component
        warnings.warn(
            f"Failed to import file '{file_path}': {type(error)} {error}"
        )
        page = _error_page_from_file_name(
            file_path,
            error_summary=f"Failed to import '{file_path}'",
            error_details=f"{type(error).__name__}: {error}",
        )
    else:
        # Search the module for the callable decorated with `@rio.page`
        pages = list[ComponentPage]()
        for obj in vars(module).values():
            try:
                pages.append(BUILD_FUNCTION_TO_PAGE[obj])
            except (TypeError, KeyError):
                pass

        if pages:
            page = pages[0]

            # More than one page found? Display a warning
            if len(pages) > 1:
                warnings.warn(
                    f"The file {file_path} contains multiple page definitions."
                    f" This is not allowed. Each page must be defined in its"
                    f" own file."
                )
        else:
            # Nothing found? Display a warning and a placeholder component
            warnings.warn(
                f"The file {file_path} doesn't seem to contain a page"
                f" definition. Did you forget to decorate your component/build"
                f" function with `@rio.page(...)`?"
            )
            page = _error_page_from_file_name(
                file_path,
                error_summary=f"No page found in '{file_path}'",
                error_details="No component in this file was decorated with `@rio.page(...)`",
            )

    # Add sub-pages, if any
    sub_pages = t.cast(list, page.children)
    sub_pages.clear()  # Avoid duplicate entries if this function is called twice
    sub_pages += auto_detect_pages(
        file_path.with_suffix(""),
        package=module_name,
    )

    return page


def _error_page_from_file_name(
    file_path: Path, error_summary: str, error_details: str
) -> ComponentPage:
    return ComponentPage(
        name=convert_case(file_path.stem, "snake").replace("_", " ").title(),
        url_segment=convert_case(file_path.stem, "kebab").lower(),
        build=functools.partial(
            rio.components.error_placeholder.ErrorPlaceholder,
            error_summary,
            error_details,
        ),
    )
