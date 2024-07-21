import rio


class DeployPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text(
                "Deploy",
                style="heading2",
                margin=1,
                justify="left",
            ),
            rio.Column(
                rio.Icon(
                    "material/rocket_launch",
                    min_width=6,
                    min_height=6,
                    margin_bottom=3,
                    fill=self.session.theme.secondary_color,
                ),
                rio.Text(
                    "One-click deployment is coming soon!",
                    justify="center",
                ),
                rio.Text(
                    "Stay tuned for updates.",
                    justify="center",
                ),
                spacing=1,
                grow_y=True,
                align_y=0.3,
                margin=1,
            ),
        )
