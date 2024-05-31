# Changelog

-   Buttons now have a smaller minimum size when using a `rio.Component` as
    content
-   `FrostedGlassFill` added (Contributed by MiniTT)
-   `rio.Fill` and `rio.FillLike` deprecated. Most components only support
    specific fills, so these have no purpose any more
-   added `@rio.event.on_window_size_change`
-   popups now default to the "hud" color
-   Add HTML meta tags
-   Add functions for reading and writing clipboard contents to the `Session`
    (Contributed by MiniTT)

## 0.8

-   Rectangles now honor the theme's shadow color
-   Renamed `Banner.markup` to `Banner.markdown`
-   Removed the "multiline" style from Banners
-   Removed `Button.initially_disabled_for`
-   Added a `text_color` parameter to `Theme.from_colors` and `Theme.pair_from_colors`
-   `rio run` now checks that the installed version of Rio is up-to-date

## 0.7

-   New example: multi-page website
-   New component: CodeBlock
-   UserSettings can now have mutable default values
-   Removed "undefined space"
