from __future__ import annotations

import logging
import typing as t
import warnings
from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path

import introspection
import path_imports
from introspection import convert_case

import rio.components.error_placeholder
import rio.docs

from . import deprecations, utils
from .errors import NavigationFailed

__all__ = [
    "Redirect",
    "ComponentPage",
    "Page",
    "page",
    "GuardEvent",
]


DEFAULT_ICON = "rio/logo:color"


@t.final
@dataclass(frozen=True)
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
    """

    url_segment: str
    target: str | rio.URL


@t.final
@dataclass(frozen=True)
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

    app.run_in_browser()
    ```

    This will display "This is the home page" when navigating to the root URL,
    but "This is a subpage" when navigating to "/subpage". Note that on both
    pages the text "Welcome to my page!" is displayed above the page content.
    That's because it's not part of the `PageView`.

    For additional details, please refer to the how-to guide:
    `https://rio.dev/docs/howto/multiple-pages`.

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
    build: t.Callable[[], rio.Component]
    _: KW_ONLY
    icon: str = DEFAULT_ICON
    children: t.Sequence[ComponentPage | Redirect] = field(default_factory=list)
    guard: t.Callable[[rio.GuardEvent], None | rio.URL | str] | None = None
    meta_tags: dict[str, str] = field(default_factory=dict)

    # This is used to allow users to order pages when using the `rio.page`
    # decorator. It's not public, but simply a convenient place to store this.
    _page_order_: int | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        # In Rio, URLs are case insensitive. An easy way to enforce this, and
        # also prevent casing issues in the user code is to make sure the page's
        # URL fragment is lowercase.
        if self.url_segment != self.url_segment.lower():
            raise ValueError(
                f"Page URL segments should be lowercase, but `{self.url_segment}` is not"
            )

        if "/" in self.url_segment:
            raise ValueError(f"Page URL segments cannot contain slashes")


# Allow using the old `page_url` parameter instead of the new `url_segment`
_old_component_page_init = ComponentPage.__init__


def _new_component_page_init(self, *args, **kwargs) -> None:
    # Rename the parameter
    if "page_url" in kwargs:
        deprecations.warn_parameter_renamed(
            since="0.10",
            old_name="page_url",
            new_name="url_segment",
            owner="rio.ComponentPage",
        )
        kwargs["url_segment"] = kwargs.pop("page_url")

    # Call the original constructor
    _old_component_page_init(self, *args, **kwargs)


ComponentPage.__init__ = _new_component_page_init


@introspection.set_signature(ComponentPage)
def Page(*args, **kwargs):
    deprecations.warn(
        since="0.10",
        message="`rio.Page` has been renamed to `rio.ComponentPage`",
    )
    return ComponentPage(*args, **kwargs)


def _get_active_page_instances(
    available_pages: t.Iterable[rio.ComponentPage | rio.Redirect],
    remaining_segments: tuple[str, ...],
) -> list[rio.ComponentPage | rio.Redirect]:
    """
    Given a list of available pages, and a URL, return the list of pages that
    would be active if navigating to that URL.
    """
    # Get the page responsible for this segment
    try:
        page_segment = remaining_segments[0]
    except IndexError:
        page_segment = ""

    for page in available_pages:
        if page.url_segment == page_segment:
            break
    else:
        return []

    active_pages = [page]

    # Recurse into the children
    if isinstance(page, rio.ComponentPage):
        active_pages += _get_active_page_instances(
            page.children,
            remaining_segments[1:],
        )

    return active_pages


@t.final
@rio.docs.mark_constructor_as_private
@dataclass(frozen=True)
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
) -> tuple[tuple[ComponentPage, ...], rio.URL]:
    """
    Check whether navigation to the given target URL is possible.

    This finds the pages that would be activated by this navigation and runs
    their guards. If the guards effect a redirect, it instead attempts to
    navigate to the redirect target, and so on.

    Raises `NavigationFailed` if navigation to the target URL is not possible
    because of an error, such as an exception in a guard.

    If the URL points to a page which doesn't exist that is not considered an
    error. The result will still be valid. That is because navigation is
    possible, it's just that some PageViews will display a 404 page.

    This function does not perform any actual navigation. It simply checks
    whether navigation to the target page is possible.
    """

    assert target_url_absolute.is_absolute(), target_url_absolute

    # Is any guard opposed to this page?
    initial_target_url = target_url_absolute
    visited_redirects = {target_url_absolute}
    past_redirects = [target_url_absolute]

    while True:
        # TODO: What if the URL is not a child of the base URL? i.e. redirecting
        #   to a completely different site
        target_url_relative = utils.make_url_relative(
            sess._base_url, target_url_absolute
        )

        # Find all pages which would by activated by this navigation
        active_page_instances = tuple(
            _get_active_page_instances(
                sess.app.pages, target_url_relative.parts
            )
        )

        # Check the guards for each activated page
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

            active_page_instances = t.cast(
                tuple[ComponentPage, ...], active_page_instances
            )

            return active_page_instances, target_url_absolute

        # A guard wants to redirect to a different page
        if isinstance(redirect, str):
            redirect = rio.URL(redirect)

        redirect = sess._active_page_url.join(redirect)

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


BuildFunction = t.Callable[[], "rio.Component"]
C = t.TypeVar("C", bound=BuildFunction)


BUILD_FUNCTIONS_FOR_PAGES = dict[BuildFunction, ComponentPage]()


def page(
    *,
    url_segment: str | None = None,
    name: str | None = None,
    icon: str = DEFAULT_ICON,
    guard: t.Callable[[GuardEvent], None | rio.URL | str] | None = None,
    meta_tags: dict[str, str] | None = None,
    order: int | None = None,
):
    """
    This decorator creates a page (complete with URL, icon, etc) that displays
    the decorated component. All parameters are optional, and if omitted,
    sensible defaults will be inferred based on the name of the decorated class.

    In order to create a "root" page, set the `url_segment` to an empty string:

        @rio.page(
            url_segment="",
        )
        class HomePage(rio.Component):
            def build(self):
                return rio.Text(
                    "Welcome to my website",
                    style="heading1",
                )

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
        BUILD_FUNCTIONS_FOR_PAGES[build] = page

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
                pages.append(BUILD_FUNCTIONS_FOR_PAGES[obj])
            except (TypeError, KeyError):
                pass

        if not pages:
            # Nothing found? Display a warning and a placeholder component
            warnings.warn(
                f"The file {file_path} doesn't seem to contain a page"
                f" definition. Did you forget to decorate your component/build"
                f" function with `@rio.page(...)`?"
            )
            page = _error_page_from_file_name(
                file_path,
                error_summary=f"No page found in '{file_path}'",
                error_details=f"No component in this file was decorated with `@rio.page(...)`",
            )
        else:
            page = pages[0]

            # More than one page found? Display a warning
            if len(pages) > 1:
                warnings.warn(
                    f"The file {file_path} contains multiple page definitions."
                    f" This is not allowed. Each page must be defined in its"
                    f" own file."
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
        build=lambda: rio.components.error_placeholder.ErrorPlaceholder(
            error_summary, error_details
        ),
    )
