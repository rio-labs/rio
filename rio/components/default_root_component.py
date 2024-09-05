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
    page: rio.Page

    def build(self) -> rio.Component:
        return rio.Rectangle(
            content=rio.Link(
                rio.Text(
                    self.page.name,
                    margin_x=OUTER_MARGIN,
                    margin_y=0.5,
                ),
                target_url=self.page.page_url,
            ),
            fill=rio.Color.TRANSPARENT,
            hover_fill=self.session.theme.neutral_palette.background_active,
            ripple=True,
            transition_time=0.1,
        )


@final
class DefaultRootComponent(component.Component):
    """
    ## Metadata

    `public`: False
    """

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
                    margin_x=OUTER_MARGIN,
                ),
                text="You can change the app name by passing `name=...` when creating the `rio.App` object.",
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
                text="You can change the description name by passing `description=...` when creating the `rio.App` object.",
            )
        )

        # Add navigation
        #
        # If this becomes any more involved, consider making it a separate
        # component
        pages = rio.Column(
            spacing=0.5,
            margin_y=3,
        )
        main_column.add(pages)

        for page in self.session.app.pages:
            pages.add(NavButton(page))

        # Push the remaining UI to the bottom
        main_column.add(rio.Spacer())

        # Explain to the user how to get rid of this navigation
        if self.session._app_server.debug_mode:
            main_column.add(
                rio.Link(
                    "What's this?",
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
            ),
            # Separator
            rio.Rectangle(
                min_width=0.3,
                fill=self.session.theme.primary_palette.background,
            ),
            # The user's content
            rio.PageView(
                grow_x=True,
            ),
        )
