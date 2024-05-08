# How can I change the appearance of my app?

Rio embraces Material Design and all included components are styled accordingly.
A big part of material design however is the ability to choose your own color
scheme. Rio makes this easy - just create a `rio.Theme` object and pass it to
your `rio.App`:

```python
import rio

# Create a theme
theme = rio.Theme.from_colors(
    primary_color=rio.Color.from_hex("b002ef"),
    secondary_color=rio.Color.from_hex("329afc"),
    light=True,
)


# Pass it to the app
app = rio.App(
    name="MyApp",
    pages=[
        ...
    ],
    theme=theme,
)
```

You can modify the colors here to fit your needs. The most important parameters
are listed, but more are available! You can find them all [in the
docs](https://rio.dev/docs/api/theme).

Tip: Bold colors tend to work best with Material design and can make your app
really stand out.

You can also provide two themes. If you do, Rio will use the first theme for
users which have their system set to light mode, and the second theme for users
which have their system set to dark mode.

```python
import rio

# Create a pair of themes
themes = rio.Theme.pair_from_colors(
    primary_color=rio.Color.from_hex("b002ef"),
    secondary_color=rio.Color.from_hex("329afc"),
)


# Pass them to the app
app = rio.App(
    name="MyApp",
    pages=[
        ...
    ],
    theme=themes,
)
```

When passing two themes, **be mindful to test your app in both light and dark
mode**. It's easy to accidentally create elements which are hard to read in one
mode or the other.

Rio's dev tools also include a theme picker. Next time you run your app using
`rio run` keep an eye out for the "Theme" option in the sidebar on the right.
