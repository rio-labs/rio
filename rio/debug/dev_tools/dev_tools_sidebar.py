from typing import *  # type: ignore

import rio.components.class_container
import rio.components.debugger_connector

from . import (
    deploy_page,
    docs_page,
    icons_page,
    project_page,
    theme_picker_page,
    tree_page,
)


class DevToolsSidebar(rio.Component):
    selected_page: (
        Literal[
            "project",
            "tree",
            "docs",
            "deploy",
        ]
        | None
    ) = None

    def get_selected_page(self) -> rio.Component | None:
        REGULAR_PAGE_WIDTH = 22
        WIDE_PAGE_WIDTH = 32

        # Nothing selected
        if self.selected_page is None:
            return None

        # Project
        if self.selected_page == "project":
            return project_page.ProjectPage(
                width=REGULAR_PAGE_WIDTH,
            )

        # Tree
        if self.selected_page == "tree":
            return tree_page.TreePage(
                width=WIDE_PAGE_WIDTH,
            )

        # Icons
        if self.selected_page == "icons":
            return icons_page.IconsPage(
                width=WIDE_PAGE_WIDTH,
            )

        # Theme
        if self.selected_page == "theme":
            return theme_picker_page.ThemePickerPage(
                width=WIDE_PAGE_WIDTH,
            )

        # Docs
        if self.selected_page == "docs":
            return docs_page.DocsPage(
                width=REGULAR_PAGE_WIDTH,
            )

        # Deploy
        if self.selected_page == "deploy":
            return deploy_page.DeployPage(
                width=REGULAR_PAGE_WIDTH,
            )

        # Anything else / TODO
        return rio.Text(
            f"TODO: {self.selected_page}",
            margin=2,
            width=REGULAR_PAGE_WIDTH,
        )

    def build(self) -> rio.Component:
        return rio.Row(
            # Big fat line to separate the debugger from the rest of the page
            rio.Rectangle(
                width=0.3,
                fill=self.session.theme.primary_palette.background,
            ),
            # Currently active page
            rio.components.class_container.ClassContainer(
                rio.Switcher(self.get_selected_page()),
                classes=["rio-switcheroo-neutral", "rio-debugger-background"],
            ),
            # Navigation
            rio.Column(
                rio.SwitcherBar(
                    names=[
                        # "Project",
                        "Tree",
                        "Icons",
                        "Theme",
                        # "Docs",
                        "Deploy",
                    ],
                    icons=[
                        # "rio/logo",
                        "material/view-quilt",
                        "material/emoji-people",
                        "material/palette",
                        # "material/library-books",
                        "material/rocket-launch",
                    ],
                    values=[
                        # "project",
                        "tree",
                        "icons",
                        "theme",
                        # "docs",
                        "deploy",
                    ],
                    allow_none=True,
                    orientation="vertical",
                    spacing=2,
                    color="primary",
                    selected_value=self.bind().selected_page,
                    margin=0.2,
                ),
                rio.Spacer(),
                rio.components.debugger_connector.DebuggerConnector(),
            ),
        )
