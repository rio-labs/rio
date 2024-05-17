from __future__ import annotations

from collections.abc import Callable
from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import utils
from .component import Component

__all__ = [
    "PageView",
]


def default_fallback_build(sess: rio.Session) -> rio.Component:
    thm = sess.theme

    return rio.Column(
        rio.Row(
            rio.Icon(
                "material/error",
                fill="warning",
                width=4,
                height=4,
            ),
            rio.Text(
                "This page does not exist",
                style=rio.TextStyle(
                    font_size=3,
                    fill=thm.warning_palette.background,
                ),
            ),
            spacing=2,
            align_x=0.5,
        ),
        rio.Text(
            "The URL you have entered does not exist on this website. Double check your spelling, or try navigating to the home page.",
            wrap=True,
        ),
        rio.Button(
            "Take me home",
            on_press=lambda: sess.navigate_to("/"),
        ),
        spacing=3,
        width=20,
        align_x=0.5,
        align_y=0.35,
    )


@final
class PageView(Component):
    """
    Placeholders for pages.

    Rio apps can consist of many pages. You might have a welcome page, a
    settings page, a login, and so on. Page views act as placeholders, that
    don't have an appearance of their own, but instead look up the currently
    active page, and display that.


    ## Attributes

    `fallback_build`: A callback that is called if the current URL does not
        correspond to any page in the application. It should return a Rio
        component that is displayed instead. If not specified Rio will
        display a default error page.


    ## Examples

    A minimal example:

    ```python
    app = rio.App(
        build=lambda: rio.Column(
            rio.Text("Welcome to my page!"),
            rio.PageView(
                width="grow",
                height="grow",
            ),
        ),
        pages=[
            rio.Page(
                "Home",
                "",
                build=lambda: rio.Text("This is the home page"),
            ),
            rio.Page(
                "Subpage",
                "subpage",
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

    """

    # TODO: Link to the routing/multipage how-to page

    _: KW_ONLY

    fallback_build: Callable[[], rio.Component] | None = None

    # How many other PageViews are above this one in the component tree. Zero
    # for top-level PageViews, 1 for the next level, and so on.
    #
    # Initialized in `__post_init__`.
    level: int = field(init=False)

    def __post_init__(self) -> None:
        self.session._page_views.add(self)

        # Determine how many `PageView`s are above this one. This can never
        # change, because `PageView`s cannot possibly be moved into or out of
        # other `PageView`s by the reconciler, since they don't accept children.
        self.level = self._find_page_view_level()

    def _find_page_view_level(self) -> int:
        """
        Follow the chain of `_weak_creator_` references to find how deep in the
        hierarchy of PageViews this one is. Returns 0 for a top-level PageView,
        1 for a PageView inside one other PageView, etc.

        Normally, following `_weak_creator_` references is not safe, because it
        can skip over other components, and even across build boundaries.
        However, since `PageView`s don't accept children, it isn't possible for
        them to ever be moved into or out of other `PageView`s by the
        reconciler.
        """
        cur_parent = self._weak_creator_()

        while True:
            # No more parents - this is the root
            if cur_parent is None:
                return 0

            # Found it
            if isinstance(cur_parent, PageView):
                return cur_parent.level + 1

            # Chain up
            cur_parent = cur_parent._weak_creator_()

    def build(self) -> rio.Component:
        # Build the active page
        #
        # Because the build function is being called inside of Rio, the
        # component is mistaken of being internal to Rio. Take care to fix that.
        try:
            page = self.session._active_page_instances[self.level]
        except IndexError:
            if self.fallback_build is None:
                result = default_fallback_build(self.session)
            else:
                result = utils.safe_build(self.fallback_build)
                result._rio_internal_ = False
        else:
            result = utils.safe_build(page.build)
            result._rio_internal_ = False

        return result
