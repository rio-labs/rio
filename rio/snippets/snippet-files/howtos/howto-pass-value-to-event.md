# Passing additional data to event handlers

Sometimes, when adding event handlers you might want to pass additional data to
an event handler. For example, if you have a row of buttons for the user to
press, you'll probably want to know which one the user clicked on. You can do so
using Python's built-in
[`functools.partial`](https://docs.python.org/3/library/functools.html#functools.partial).

```python
import functools


class MyComponent(rio.Component):
    def on_button_press(self, data: str) -> None:
        print(f"The user pressed {data}")

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Button(
                "First Button",
                on_press=functools.partial(self.on_button_press, "Button 1"),
            ),
            rio.Button(
                "Second Button",
                on_press=functools.partial(self.on_button_press, "Button 2"),
            )
        )
```
