# How do I create my own component?

Creating your own components is simple! Just inherit from `rio.Component`, and
write your class as though it were a `dataclass`. The only required method is
`build`.

```python
class MyComponent(rio.Component):
    # First, list the properties of your component. These are also called the
    # component's `state`.
    #
    # All Rio components are automatically dataclasses, so you don't have to
    # write your own `__init__`. It's already been done for you!
    title: str
    description: str

    # Each component has a `build` method. Here, you construct the user
    # interface for your component by returning other, more fundamental
    # components.
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text(self.title, style='heading1'),
            rio.Text(self.description),
        )
```
