# Can I create a website using Rio?

Yes! Rio supports both websites and local apps. The code to create the two is
completely the same. The only difference is in how you run your project.

Here's a quick example:

```python
import rio

class MyComponent(rio.Component):
    def build(self) -> rio.Component:
        return rio.Text("Welcome to my first App!")

app = rio.App(
    name="My First App",
    build=MyComponent,
)

if __name__ == "__main__":
    # To run as website
    app.run_as_web_server()

    # To run as website and immediately open a browser
    app.run_in_browser()

    # Or as local app
    app.run_in_window()
```

The page on [deploying your app](https://rio.dev/docs/howtos/deployment) has
additional details on deploying your app as website.
