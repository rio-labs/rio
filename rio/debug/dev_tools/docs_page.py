import rio


class DocsPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text(
                "Documentation",
                style="heading2",
                margin=1,
                justify="left",
            ),
            rio.Column(
                rio.Text(
                    "New here? The Rio tutorial can help you get started.",
                    wrap=True,
                ),
                rio.Button(
                    "Read the Tutorial",
                    icon="material/school",
                    style="minor",
                    margin=1,
                    on_press=self._open_tutorial,
                ),
                spacing=1,
                height="grow",
                align_y=0.5,
                margin=1,
            ),
        )

    async def _open_tutorial(self) -> None:
        await self.session._evaluate_javascript("""
window.open('https://rio.dev/get-started', '_blank');
""")
