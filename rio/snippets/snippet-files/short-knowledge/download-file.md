# How can I save or download a file?

The `Session` is your friend! Inside of any `rio.Component`, call
`self.session.save_file`. If you're running as a website, this will start a
download. If you're running as a desktop app, this will open a file dialog.

```python
class MyComponent(rio.Component):
    async def on_button_press(self) -> None:
        await self.session.save_file(
            file_contents="Hello, world!",
            name="hello.txt",
        )

    def build(self) -> rio.Component:
        return rio.Button(
            "Save file",
            on_press=self.on_button_press,
        )
```
