from typing import *  # type: ignore

import rio


class HistoryItem(rio.Component):
    from_string: str
    to_string: str
    title: str
    organization: str
    details: str
    icon: str

    is_open: bool = False

    def on_press(self) -> None:
        self.is_open = not self.is_open

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Row(
                rio.Icon(
                    self.icon,
                    width=3,
                    height=3,
                    margin_right=2,
                    align_x=0,
                    align_y=0,
                ),
                rio.Column(
                    rio.Text(
                        f"{self.from_string} - {self.to_string}",
                        align_x=0,
                        style=rio.TextStyle(fill=rio.Color.GREY),
                    ),
                    rio.Text(
                        f"{self.title} at {self.organization}",
                        style="heading3",
                        align_x=0,
                    ),
                    rio.Revealer(
                        None,
                        rio.Text(
                            self.details,
                            multiline=True,
                            align_x=0,
                        ),
                        is_open=self.is_open,
                    ),
                    spacing=0.3,
                    width="grow",
                    align_y=0,
                ),
            ),
            on_press=self.on_press,
        )


class History(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text(
                "Professional Experience",
                style="heading2",
                margin_top=3,
            ),
            HistoryItem(
                "2021",
                "Present",
                "AI Researcher",
                "DataWorks Inc.",
                "Developed and deployed machine learning models to improve the "
                "accuracy of the company's recommender system. Collaborated "
                "with a team of 10 researchers to implement a novel algorithm "
                "for predicting user behavior.",
                "science",
            ),
            HistoryItem(
                "2018",
                "2021",
                "Data Analyst",
                "Insight Technologies",
                "Conducted in-depth data analysis and implemented machine "
                "learning algorithms to improve predictive models, resulting "
                "in a 15% increase in accuracy. Collaborated with "
                "cross-functional teams to develop and deploy scalable AI "
                "solutions for optimizing business operations.",
                "monitoring",
            ),
            rio.Text(
                "Education",
                style="heading2",
                margin_top=3,
            ),
            HistoryItem(
                "2015",
                "2018",
                "Master in Data Science",
                "Carnegie Mellon University, Pittsburgh, PA",
                'Thesis: "Predictive Modeling in Financial Markets using '
                'Machine Learning Techniques"',
                "school",
            ),
            HistoryItem(
                "2012",
                "2015",
                "Bachelor in Software Engineering",
                "University of Texas, Austin, TX",
                'Thesis: "Design and Implementation of an Intelligent Traffic '
                'Control System"',
                "school",
            ),
            spacing=2,
        )
