from __future__ import annotations

from typing import *  # type: ignore

import rio

from . import component

__all__ = ["DefaultRootComponent"]


OUTER_MARGIN = 0.8


def with_debug_tooltip(
    session: rio.Session,
    comp: component.Component,
    text: str,
) -> rio.Component:
    """
    Wraps the given component in a tooltip which only shows up if the app is
    running in debug mode. This allows you to provide additional information to
    users without disrupting their production site.
    """

    if session._app_server.debug_mode:
        return rio.Tooltip(
            anchor=comp,
            tip=text,
            position="right",
        )

    return comp


@final
class Welcome(component.Component):
    def build(self) -> rio.Component:
        # TODO:
        #
        # - Link to the tutorial & documentation
        # - Explain how to add a page, or link to a how-to which does that
        # - Add a button/form which adds a page to the app
        # - Make extra fluffy pancakes
        return rio.Column(
            rio.Text(
                "Welcome to your Rio app!",
                style="heading1",
            ),
            rio.Text("Very TODO"),
            spacing=0.5,
            align_y=0.5,
        )


@final
class NavButton(component.Component):
    page: rio.ComponentPage
    is_current: bool

    def build(self) -> rio.Component:
        main_row = rio.Row()

        # Add a marker if this is the current page
        if self.is_current:
            marker = rio.Rectangle(
                fill=self.session.theme.primary_color,
                min_width=0.5,
                align_x=0,
                corner_radius=(0, 1, 1, 0),
            )
        else:
            marker = None

        main_row.add(
            rio.Switcher(
                marker,
                transition_time=0.1,
            )
        )

        # Prepare the base UI
        main_row.add(
            rio.Rectangle(
                content=rio.Link(
                    rio.Text(
                        self.page.name,
                        style=rio.TextStyle(
                            font_weight="bold" if self.is_current else "normal",
                        ),
                        selectable=False,
                        margin_x=OUTER_MARGIN,
                        margin_y=0.5,
                    ),
                    target_url=f"/{self.page.url_segment}",
                ),
                fill=rio.Color.TRANSPARENT,
                hover_fill=None
                if self.is_current
                else self.session.theme.neutral_palette.background_active,
                ripple=True,
                transition_time=0.1,
                grow_x=True,
            )
        )

        return main_row


@final
class DefaultRootComponent(component.Component):
    """
    ## Metadata

    `public`: False
    """

    @rio.event.on_page_change
    async def _on_page_change(self) -> None:
        await self.force_refresh()

    def build(self) -> rio.Component:
        # Special case: If the app has no pages at all, display a warm welcome.
        if len(self.session.app.pages) == 0:
            return Welcome()

        # Special case: If the app only has a single page, don't spawn any
        # navigation.
        if len(self.session.app.pages) == 1:
            return rio.PageView()

        # Regular case: Display a proper navigation
        #
        # Build up the main column
        main_column = rio.Column(
            spacing=0.5,
            margin_y=OUTER_MARGIN,
            min_width=20,
        )

        # App name
        main_column.add(
            with_debug_tooltip(
                session=self.session,
                comp=rio.Text(
                    self.session.app.name,
                    style="heading1",
                    overflow="wrap",
                    margin_left=OUTER_MARGIN,
                    # Leave some space for the curved corner
                    margin_right=OUTER_MARGIN
                    + self.session.theme.corner_radius_large,
                ),
                text="You can change the app name by passing `name=...` when creating your `rio.App` object.",
            )
        )

        # App description
        main_column.add(
            with_debug_tooltip(
                session=self.session,
                comp=rio.Text(
                    self.session.app.description,
                    overflow="wrap",
                    margin_x=OUTER_MARGIN,
                ),
                text="You can change the app description by passing `description=...` when creating your `rio.App` object.",
            )
        )

        # Which page is currently active?
        # Prepare the URL
        segments = self.session.active_page_url.parts

        # Special case: Not deep enough
        if len(segments) <= 1:
            # This won't match anything because it's not a valid URL segment"
            current_page_url = "///"
        else:
            current_page_url = segments[1]

        # Add navigation
        #
        # If this becomes any more involved, consider making it a separate
        # component
        pages = rio.Column(
            spacing=0.5,
            margin_y=1.5,
        )
        main_column.add(pages)

        for page in self.session.app.pages:
            pages.add(
                NavButton(
                    page,
                    is_current=page.url_segment == current_page_url,
                )
            )

        # Push the remaining UI to the bottom
        main_column.add(rio.Spacer())

        # Explain to the user how to get rid of this navigation
        if self.session._app_server.debug_mode:
            main_column.add(
                rio.Link(
                    "What's this?",
                    icon="material/library_books",
                    target_url="https://rio.dev/TODO/LINK/TO/HOWTO/REMOVE/NAVIGATION",
                    open_in_new_tab=True,
                    margin_x=OUTER_MARGIN,
                    margin_y=1,
                    align_x=0.5,
                )
            )

        # We are the coolest!
        main_column.add(
            rio.Link(
                rio.Row(
                    rio.Icon(
                        "rio/logo:color",
                        # fill="dim",
                        min_width=2,
                    ),
                    rio.Text(
                        "Built with Rio\nWebsites & apps in 100% Python",
                        justify="left",
                        style="dim",
                        grow_x=True,
                        # Leave some space for the curved corner
                        margin_right=self.session.theme.corner_radius_large,
                    ),
                    align_x=0.5,
                    spacing=0.5,
                ),
                target_url="https://rio.dev",
                margin_x=OUTER_MARGIN,
            )
        )

        # Build the UI
        return rio.Row(
            # Sidebar
            rio.Rectangle(
                content=main_column,
                fill=self.session.theme.neutral_color,
                corner_radius=(
                    0,
                    self.session.theme.corner_radius_large,
                    self.session.theme.corner_radius_large,
                    0,
                ),
                margin=0.5,
                margin_left=0,
            ),
            # The user's content
            rio.PageView(
                grow_x=True,
            ),
        )
