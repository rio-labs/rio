# How do I pass values between components?

When creating apps with Rio, you'll often find yourself in situations where you
need to pass values between components. This can be as simple as passing a
string to a text input, or as complex as sharing a value across many components
and keeping them all up-to-date.

## Parent to Child

```plain
Parent Component        ┐
│                       │
├── Child Component 1  ◄┘
│
└── Child Component 2
```

If you have a value in a component, and want to pass it to one of its children,
you can simply pass it as a parameter to the child component:

```python
class CustomComponent(rio.Component):
    some_value: str

    def build(self) -> rio.Component:
        return rio.TextInput(
            text=self.some_value,
        )

```

## Child to Parent

```plain
Parent Component       ◄┐
│                       │
├── Child Component 1   ┘
│
└── Child Component 2
```

But what if we wanted to pass a value in the other direction? After the user
enters a text, we need to be able to get the modified value after all, so we can
store it in a database, send it to a server, or whatever else we need to do with
it.

This is where one of Rio's coolest features comes in - Attribute bindings! Let's
take a look at code:

```python
class CustomComponent(rio.Component):
    some_value: str

    def _on_button_press(self) -> None:
        # Just read the local value. Thanks to the attribute binding below it
        # will always be up-to-date
        print(self.some_value)

    def build(self) -> rio.Component:
        return rio.Column(
            rio.TextInput(
                # By using `self.bind().some_value` instead of `self.some_value`,
                # we're instructing Rio to create a connection between the parent
                # and child components. This means that if the value in either
                # of the components changes, the other one will be updated
                # automatically for us!
                #
                # So, if the user types something into the TextInput, the value
                # will be updated in both the TextInput itself, as well as
                # our own component.
                text=self.bind().some_value,
            ),
            rio.Button(
                "Click me!",
                on_press=self._on_button_press,
            ),
        )
```

The code looks fairly similar to the previous example, but with one key
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

```plain
Parent Component
│
├── Child Component 1   ┐
│                       │
└── Child Component 2  ◄┘
```

Passing values between siblings doesn't require any new concepts. Simply bind
both components to the same parent attribute and all three will be kept in sync:

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

Here, changing either of the inputs will update the other one. (You might have
to press `Enter ⏎` or click outside the input to see the change.)

## Session Attachments

In larger projects you'll often find yourself in situations where you need to
share a value across many components. If only a few components are involved you
can simply pass the value as a parameter to the components. However, if you have
many components that need access to the same value, you can use the session to
store the value and access it from any component.

Rio sessions have dictionary-like capabilities. You can "attach" values to them,
and retrieve them later. Here's an example attaching user information to the
session:

```python
from dataclasses import dataclass

@dataclass
class UserData:
    name: str


# Inside of your component:
class MyComponent(rio.Component):
    ...

    def attach_value(self) -> None:
        user_data = UserData(name="John Doe")
        self.session.attach(user_data)
        ...


    def get_value(self) -> None:
        user_data = self.session[UserData]
        print(user_data.name)
        ...
```

Common use cases for attachments are:

-   **Database connections**: Attach a database connection to the session, so that
    all components can access it.

-   **User authentication**: When the user logs in, attach the logged in user's
    name and id to the session. This way, every component always knows which user
    it's talking to.

-   **Per-user Settings**: Any classes which inherit from `rio.UserSettings` will
    be stored persistentnly on the user's device. This means they'll still be
    present when the user visits your app again later.

    Please note that some countries have strict laws about storing user data. You
    might have to ask for the user's consent before storing any data on their
    device. Please do some research on this topic before implementing user
    settings.
