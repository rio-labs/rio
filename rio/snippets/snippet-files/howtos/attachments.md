# Can I share values in a session? / Does Rio Support Dependency Injection?

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

Common use cases for attachments:

- **User authentication**: When the user logs in, attach the user's information
  to the session. This way, every component always knows which user it's talking
  to.
- **Per-user Settings**: Rio has special support for
