# How do I create custom events?

Events are a core concept used throughout Rio. If you've written even a small
app you'll have used them to react to button presses, changing text inputs and
many other user interactions. Sometimes though, you'll want to create your own
events.

Creating your own events is a breeze. Just make some space for a handler and
annotate it as `rio.EventHandler`:

```python
class MyComponent:
    # This property will store the event handler. Since we aren't passing any
    # values to the handler, it's annotated as `rio.EventHandler[[]]`.
    #
    # If you were to pass a value, say an `int` to the handler, you'd annotate
    # it as `rio.EventHandler[int]`.
    on_press: rio.EventHandler[[]] = None

    # This function will be called by the button when it's pressed. We'll use it
    # to trigger our own event.
    async def _on_press(self):
        # Rio has a built-in convenience function for calling event handlers.
        # This function will prevent your code from crashing if something
        # happens in the event handler, and also allows for the handler to be
        # both synchronous and asynchronous.
        await self.call_event_handler(self.on_press)

    def build(self) -> rio.Component:
        # Create a button that will trigger our event handler when pressed.
        return rio.Button(
            "Squeak!",
            on_press=self._on_press
        )
```
