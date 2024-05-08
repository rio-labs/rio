# How do I Pass Values Between Components?

## Parent to Child

When creating apps with Rio, values frequently need to be passed between
components. For example, you may pass a string value to a `TextInput` component
like this

```python
class CustomComponent(rio.Component):
    def build(self) -> rio.Component:
        return rio.TextInput(
            text="Hello world!",
        )

```

This is the simplest case. There is nothing special going on here - we're just
passing a string value to a class.

## Child to Parent

But what if we wanted to pass a value in the other direction? After the user
enters a text, we need to be able to get the modified value after all, so we can
store it in a database, send it to a server, or whatever else we need to do with
it.

This is where one of Rio's coolest features comes in - State bindings! Let's
take a look at code:

```python
class CustomComponent(rio.Component):
    some_value: str

    def _on_button_press(self) -> None:
        # Just read the local value. Thanks to the state binding below it will
        # always be up-to-date
        print(self.some_value)

    def build(self) -> rio.Component:
        return rio.Column(
            rio.TextInput(
                # By using `self.bind().some_value` instead of `self.some_value`,
                # we're instructing Rio to create a connection between the parent
                # and child components. This means that if the value in either
                # of the components changes, the other one will be updated
                # automatically for us!
                text=self.bind().some_value,
            ),
            rio.Button(
                "Click me!",
                on_press=self._on_button_press,
            ),
        )
```

The results looks fairly similar to the previous example, but with one key
difference: Notice how the `some_value` value we're passing to the `TextInput`
component is written as `self.bind().some_value` instead of `self.some_value`?
By using `.bind()` we're telling Rio that we don't just want to pass the current
value to the child, but for Rio to create a connection between the parent and
child components.

If either of the components now assigns a new value to `some_value`, the other
component will automatically be updated with the new value, without any extra
code on our part!

So now, if you want to get the value of the `TextInput` component, you can just
write `self.some_value` and it will always contain the up-to-date value of the
`TextInput` component. That is exactly what we're doing in the button's event
handler.

## Sibling to Sibling

Passing values between siblings doesn't require any new concepts. Simply bind
both components to the same class property, and they will be kept in sync:

```python
class CustomComponent(rio.Component):
    some_value: str

    def build(self) -> rio.Component:
        return rio.Column(
            rio.TextInput(
                text=self.bind().some_value,
            ),
            rio.TextInput(
                text=self.bind().some_value,
            ),
            spacing=1,
        )

```

        result.markdown(
            """
Here, changing either of the inputs will update the other one. (You might have
to press `Enter ⏎` or click outside the input to see the change.)
    """
        )

        return result
