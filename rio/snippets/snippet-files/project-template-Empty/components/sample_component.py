import rio


# <component>
class SampleComponent(rio.Component):
    """
    This is a sample component. Components are the building blocks of Rio apps.

    Tip: An easy way to add components to your project is using the `rio`
    command:

    ```bash
    rio add component
    ```
    """

    pressed: bool = False

    def on_press(self) -> None:
        self.pressed = True

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text(
                "Pressed!" if self.pressed else "This is a sample component",
            ),
            rio.Button(
                "Press me!",
                on_press=self.on_press,
            ),
            spacing=1,
            align_x=0.5,
            align_y=0.5,
        )


# </component>
