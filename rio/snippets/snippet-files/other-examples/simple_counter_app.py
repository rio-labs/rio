import rio


# <counter>
# <class-header>
class Counter(rio.Component):
    value: int = 0
    # </class-header>

    # <event-handlers>
    def _on_increment(self) -> None:
        self.value += 1

    def _on_decrement(self) -> None:
        self.value -= 1

    def _on_reset(self) -> None:
        self.value = 0

    # </event-handlers>

    # <build>
    def build(self):
        return rio.Column(
            rio.Row(
                rio.IconButton(
                    "material/remove",
                    on_press=self._on_decrement,
                    size=3,
                ),
                rio.Text(
                    str(self.value),
                    style="heading1",
                    width=5,
                ),
                rio.IconButton(
                    "material/add",
                    on_press=self._on_increment,
                    size=3,
                ),
                spacing=3,
            ),
            rio.Button(
                "Reset",
                style="minor",
                on_press=self._on_reset,
            ),
            spacing=2,
            align_x=0.5,
            align_y=0.5,
        )


# </build>
# </counter>


# <app>
app = rio.App(
    pages=[
        rio.Page("Home", "", Counter),
    ],
)
# </app>

# <run>
app.run_in_browser()
# </run>
