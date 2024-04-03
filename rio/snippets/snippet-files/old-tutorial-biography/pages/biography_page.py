from typing import *  # type: ignore

import rio

from .. import components as comps


class BiographyPage(rio.Component):
    def build(self) -> rio.Component:
        thm = self.session.theme

        return rio.Column(
            rio.Rectangle(
                style=rio.BoxStyle(
                    fill=rio.LinearGradientFill(
                        (thm.primary_palette.background, 0),
                        (thm.primary_palette.background.brighter(0.2), 1),
                    )
                ),
                height=1.0,
            ),
            rio.Column(
                comps.AboutMe(),
                rio.Grid(
                    (
                        comps.Contact(
                            "123 Main Street, Anytown, USA 12345",
                            "location-on",
                        ),
                        comps.Contact(
                            "Gitlab",
                            rio.URL(
                                "https://about.gitlab.com/images/press/logo/svg/gitlab-logo-500.svg"
                            ),
                            link=rio.URL("https://gitlab.com"),
                        ),
                    ),
                    (
                        comps.Contact(
                            "(123) 456-7890",
                            "call:fill",
                        ),
                        comps.Contact(
                            "GitHub",
                            rio.URL(
                                "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
                            ),
                            link=rio.URL("https://github.com"),
                        ),
                    ),
                    (
                        comps.Contact(
                            "janedoe@email.com",
                            "mail",
                            link=rio.URL("mailto:janedoe@email.com"),
                        ),
                        comps.Contact(
                            "LinkedIn",
                            rio.URL(
                                "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/LinkedIn_logo_initials.png/768px-LinkedIn_logo_initials.png"
                            ),
                            link=rio.URL("https://linkedin.com"),
                        ),
                    ),
                    row_spacing=1.5,
                    column_spacing=5,
                    width="grow",
                    margin_y=2,
                ),
                rio.Row(
                    comps.SkillBars(
                        {
                            "Python": 5,
                            "Rust": 3,
                            "SQL": 4,
                            "R": 3,
                        },
                        width="grow",
                        align_y=0,
                    ),
                    comps.SkillBars(
                        {
                            "Pandas": 5,
                            "Numpy": 5,
                            "SciPy": 3,
                            "Matplotlib": 4,
                            "Seaborn": 4,
                        },
                        width="grow",
                        align_y=0,
                    ),
                    comps.SkillBars(
                        {
                            "English": 5,
                            "Spanish": 3,
                            "French": 2,
                        },
                        width="grow",
                        align_y=0,
                    ),
                    width="grow",
                    spacing=5,
                ),
                comps.History(margin_x=10),
                rio.Text(
                    "Personal Projects",
                    style="heading2",
                    margin_x=8,
                    margin_top=3,
                ),
                comps.Projects(),
                rio.Overlay(
                    rio.IconButton(
                        icon="mail:fill",
                        margin_right=3,
                        margin_bottom=3,
                        align_x=1,
                        align_y=1,
                    )
                ),
                margin_y=4,
                spacing=2,
                width=40,
                align_x=0.5,
            ),
            align_y=0,
        )
