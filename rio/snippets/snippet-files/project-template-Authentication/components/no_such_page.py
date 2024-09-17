import rio


# <component>
class NoSuchPage(rio.Component):
    """
    This component will be displayed when the user navigates to a page that does
    not exist.

    Think of it as a 404 page.
    """

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon(
                        "material/error",
                        fill="warning",
                        min_width=4,
                        min_height=4,
                    ),
                    rio.Text(
                        "This page does not exist!",
                        style=rio.TextStyle(
                            font_size=3,
                            fill=self.session.theme.warning_palette.background,
                        ),
                    ),
                    spacing=2,
                    align_x=0.5,
                ),
                rio.Text(
                    "The entered URL does not exist on this website. Please check your input or navigate back to the homepage.",
                    wrap=True,
                ),
                rio.Button(
                    "To homepage",
                    on_press=lambda: self.session.navigate_to("/"),
                ),
                spacing=3,
                margin=4,
                min_width=20,
            ),
            color="primary",
            align_x=0.5,
            align_y=0.35,
        )


# </component>
