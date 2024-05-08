# How do I pass additional data to an event handler?

Sometimes, when adding event handlers you might want to pass additional data to
an event handler. You can do so using `functools.partial`.

```python
from functools import partial

class MyComponent(rio.Component):
    def on_button_press(self, data: str) -> None:
        print(f"The user has pressed the button with data: {data}")

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Button(
                "Press me",
                on_press=partial(self.on_button_press, "Button 1"),
            ),
            rio.Button(
                "And me",
                on_press=partial(self.on_button_press, "Button 2"),
            )
        )
```
