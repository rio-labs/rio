# How can I remove the default navigation bar?

If your app has multiple pages, a default navigation bar will automatically be
displayed.

```python
app = rio.App(
    pages=[
        rio.ComponentPage(
            name="Home",
            url_segment="",
            build=lambda: rio.Markdown("Welcome to your Home Page!"),
        ),
        rio.ComponentPage(
            name="About Us",
            url_segment="about-page",
            build=lambda: rio.Markdown("This page provides information about our company."),
        ),
    ],
)
```

To disable the default navigation bar, simply add a `build` method to your `App`
class.

```python
app = rio.App(
    # Add a build method to your App class
    build=lambda: rio.PageView(grow_y=True), # <-- Will remove the default navigation bar
    pages=[
        rio.ComponentPage(
            name="Home",
            url_segment="",
            build=lambda: rio.Markdown("Welcome to your Home Page!"),
        ),
        rio.ComponentPage(
            name="About Us",
            url_segment="about-page",
            build=lambda: rio.Markdown("This page provides information about our company."),
        ),
    ],
)

```

For details on styling your navigation bar and creating a custom build function,
refer to [Multipage Example](https://rio.dev/examples/multipage-website).
