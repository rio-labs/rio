# How can I open or upload a file?

The `Session` is your friend! Inside of any `rio.Component`, call
`self.session.file_chooser`. This will open a file chooser dialog on the user's
device and return the path to the file (or files) they select.

```python
class MyComponent(rio.Component):
    async def on_button_press(self) -> None:
        # Let the user select a file. The result is a `FileInfo` object.
        try:
            file_info = await self.session.file_chooser()
        except rio.NoFileSelectedError:
            return

        # `FileInfo` contains information such as the file's name, as well as
        # methods for retrieving the file's contents.
        print(f"The user has selected {file_info.name}. Here are the file's contents:")
        print(file_info.read_text())

    def build(self) -> rio.Component:
        return rio.Button(
            "Select file",
            on_press=self.on_button_press,
        )
```
