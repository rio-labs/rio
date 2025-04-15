# Changelog

## unreleased

-   Components that depend on session attributes (like `active_page_url`) or
    session attachments are now automatically rebuilt when those values change
-   Components are now rebuilt immediately after a state change, not just after
    event handlers
-   `NumberInput` can now evaluate math expressions
-   `PointerEventListener` can now listen to only specific button events
-   `KeyEventListener` can now listen to only specifc hotkeys
-   `Calendar` now has a `is_sensitive` parameter
-   New component: `rio.PdfViewer`
-   The `CursorStyle` enum is deprecated in favor of string literals
-   Added `accessibility_role` parameter to all components
-   Added 'accessibility_relationship' parameter to `Link` component

## 0.11

-   Added `tile` fill mode to `rio.ImageFill`
-   `Component.force_refresh` is now synchronous
-   Added `tile` fill mode to `rio.ImageFill`
-   Colors now use Oklab instead of RGB
-   Breaking: `rio.Color.hex` now returns a 6-digit hex code instead of an
    8-digit one. Use `rio.Color.hexa` to get the old behavior.
-   Dialogs now apply a style by default
-   `rio.Drawer` now sizes itself to not only fit the anchor, but also the
    drawer content
-   `rio.Popup` now accepts `user_closable` and `modal`, just like dialogs
-   more styling options for cells in `rio.Table`

-   Expose additional platform information:

    -   `rio.Session.screen_width`
    -   `rio.Session.screen_height`
    -   `rio.Session.pixels_per_font_height`
    -   `rio.Session.scroll_bar_size`
    -   `rio.Session.primary_pointer_type`

-   Themes now take an additional `header_font` parameter

-   Breaking: Gradient stops can now be specified just as colors and Rio will
    infer their position (breaking, because the stops must be ordered now)

-   add icons for common brands

## ???

-   New styles for input boxes: "rounded" and "pill"
-   Improved mobile support: Dragging is now much smoother
-   Improved tables
-   `rio run` now also works when using `as_fastapi`

## 0.10

-   `rio.Dropdown` will now open a fullscreen popup on mobile devices
-   `rio.MediaPlayer` now also triggers the `on_playback_end` event when the
    video loops
-   experimental support for base-URL
-   dialogs!
-   dialogs can now store a result value similar to futures
-   `rio.Text.wrap` is now `rio.Text.overflow`. Same for markdown.
-   removed `rio.Popup.on_open_or_close`. This event never actually fired.
-   `rio.Link` can now optionally display an icon
-   Rio will automatically create basic navigation for you, if your app has more
    than one page
-   Updated button styles: Added `colored-text` and renamed `plain` ->
    `plain-text`
-   Methods for creating dialogs are now in `rio.Session` rather than
    `rio.Component`.
-   Page rework
    -   Add `rio.Redirect`
    -   TODO: Automatic page scan
-   New experimental `rio.FilePickerArea` component

## 0.9.2

-   restyled `rio.Switch`
-   New ~~experimental~~ broken component `AspectRatioContainer`

## 0.9.1

-   added gain_focus / lose_focus events to TextInput and NumberInput
-   `.rioignore` has been superseeded by the new `project-files` setting in
    `rio.toml`
-   values in `rio.toml` are now written in kebab-case instead of
    all_lower_case. Rio will still recognize the old names and automatically fix
    them for you.
-   deprecated `light` parameter of `Theme.from_color`, has been superseded by
    `mode`
-   Tooltips now default to `position="auto"`
-   Icons now use `_` instead of `-` in their names. This brings them more in line
    with Python naming conventions
-   Checkbox restyling

## 0.9

-   Buttons now have a smaller minimum size when using a `rio.Component` as
    content
-   `FrostedGlassFill` added (Contributed by MiniTT)
-   added `@rio.event.on_window_size_change`
-   popups now default to the "hud" color
-   popups and tooltips are no longer cut off by other components
-   Add HTML meta tags
-   Add functions for reading and writing clipboard contents to the `Session`
    (Contributed by MiniTT)
-   The color of drawers is now configurable, and also sets the theme context
-   added `Calendar` component
-   added `DateInput` component
-   massive dev-tools overhaul
-   new (but experimental) `Switcher` component
-   TextInputs now update their text in real-time
-   `rio run` no longer opens a browser
-   `rio.HTML` components now execute embedded `<script>` nodes
-   added `Checkbox` Component
-   `FlowContainer` now has a convenience `spacing` parameter which controls both
    `row_spacing` and `column_spacing` at the same time

deprecations:

-   `rio.Fill` and `rio.FillLike` deprecated. Most components only support
    specific fills, so these have no purpose any more
-   `display_controls` parameter of `CodeBlock` component renamed to
    `show_controls`

breaking:

-   `Text.justify` now defaults to `"left"`
-   `FlowContainer.justify` now defaults to `"left"`
-   `rio.Theme` is no longer frozen, and can now be modified. This is breaking,
    because the `replace` method has been removed

## 0.8

-   Rectangles now honor the theme's shadow color
-   Renamed `Banner.markup` to `Banner.markdown`
-   Removed the "multiline" style from Banners
-   Removed `Button.initially_disabled_for`
-   Added a `text_color` parameter to `Theme.from_colors` and
    `Theme.pair_from_colors`
-   `rio run` now checks that the installed version of Rio is up-to-date

## 0.7

-   New example: multi-page website
-   New component: CodeBlock
-   UserSettings can now have mutable default values
-   Removed "undefined space"
