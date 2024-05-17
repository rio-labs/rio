from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import KW_ONLY, dataclass, field
from typing import final

import rio

from . import utils
from .errors import NavigationFailed

__all__ = ["Page"]


@final
@dataclass(frozen=True)
class Page:
    """
    A routable page in a Rio app.

    Rio apps can consist of many pages. You might have a welcome page, a
    settings page, a login, and so on. `Page` components contain all information
    needed to display those pages, as well as to navigate between them.

    This is not just specific to websites. Apps might, for example, have
    a settings page, a profile page, a help page, and so on.

    Pages are passed directly to the app during construction, like so:

    ```python
    import rio

    app = rio.App(
        build=lambda: rio.Column(
            rio.Text("Welcome to my app!"),
            rio.PageView(height="grow"),
        ),
        pages=[
            rio.Page(
                name="Home",
                page_url="",
                build=lambda: rio.Text("This is the home page"),
            ),
            rio.Page(
                name="Subpage",
                page_url="subpage",
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

    TODO: Link to the routing/multipage how-to page

    ## Attributes

    `name`: A human-readable name for the page. While the page itself doesn't
        use this value directly, it serves as important information for
        debugging, as well as other components such as navigation bars.

    `page_url`: The URL segment at which this page should be displayed. For
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
        `page_url` is "page1", and it has a child page with `page_url` "page2",
        then the child page will be displayed at
        "https://yourapp.com/page1/page2".

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
    page_url: str
    build: Callable[[], rio.Component]
    _: KW_ONLY
    icon: str = "rio/logo:color"
    children: list[Page] = field(default_factory=list)
    guard: (
        Callable[[rio.Session, tuple[rio.Page, ...]], None | rio.URL | str]
        | None
    ) = None

    def __post_init__(self) -> None:
        # URLs are case insensitive. An easy way to enforce this, and also
        # prevent casing issues in the user code is to make sure the page's URL
        # fragment is lowercase.
        if self.page_url != self.page_url.lower():
            raise ValueError(
                f"Page URLs have to be lowercase, but `{self.page_url}` is not"
            )


def _get_active_page_instances(
    available_pages: Iterable[rio.Page],
    remaining_segments: tuple[str, ...],
) -> list[rio.Page]:
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
        if page.page_url == page_segment:
            break
    else:
        return []

    # Recurse into the children
    sub_pages = _get_active_page_instances(
        page.children,
        remaining_segments[1:],
    )
    return [page] + sub_pages


def check_page_guards(
    sess: rio.Session,
    target_url_absolute: rio.URL,
) -> tuple[tuple[Page, ...], rio.URL]:
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
        for page in active_page_instances:
            if page.guard is None:
                continue

            try:
                redirect = page.guard(sess, active_page_instances)
            except Exception as err:
                message = f"Rejecting navigation to `{initial_target_url}` because of an error in a page guard of `{page.page_url}`: {err}"
                logging.exception(message)
                raise NavigationFailed(message)

            if redirect is not None:
                break

        # All guards are satisfied - done
        if redirect is None:
            return active_page_instances, target_url_absolute

        # A guard wants to redirect to a different page
        if isinstance(redirect, str):
            redirect = rio.URL(redirect)

        redirect = sess._active_page_url.join(redirect)

        assert redirect.is_absolute(), redirect

        # Detect infinite loops and break them
        if redirect in visited_redirects:
            page_strings = [
                str(page_url) for page_url in past_redirects + [redirect]
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
