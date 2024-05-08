# What is a session?

On websites, every time a user connects to your website, a new session is
created. Local apps work the same, but there is only one session - since only
one user can use the app at a time.

Thus, you can think of each session representing a single user. The session
contains information relevant to the app state for that user, such as which page
they're currently on, the active theme (light or dark), and so on.

You can always access the session using `self.session` inside of any
`rio.Component`.

```python
import rio

class Counter(rio.Component):
    value: int = 0

    def _on_increment(self) -> None:
        self.value += 1

    def _on_decrement(self) -> None:
        self.value -= 1

    def _on_reset(self) -> None:
        self.value = 0

    def build(self):
        return rio.Column(
            rio.Row(
                rio.Button(
                    "-1", on_press=self._on_decrement,
                ), rio.Text(
                    str(self.value), style="heading1", width=5,
                ), rio.Button(
                    "+1", on_press=self._on_increment,
                ), spacing=3,
            ), rio.Button(
                "Reset", style="minor", on_press=self._on_reset,
            ), spacing=2, align_x=0.5, align_y=0.5,
        )
```
