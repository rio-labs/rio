# Changelog

- added gain_focus / lose_focus events to TextInput and NumberInput
- deprecated `light` parameter of `Theme.from_color`, has been superseded by
    `mode`
- `.rioignore` has been superseeded by the new `project-files` setting in
    `rio.toml`
- values in `rio.toml` are now written in kebab-case instead of
    all_lower_case. Rio will still recognize the old names and automatically fix
    them for you.

## 0.9

- Buttons now have a smaller minimum size when using a `rio.Component` as
    content
- `FrostedGlassFill` added (Contributed by MiniTT)
- `rio.Fill` and `rio.FillLike` deprecated. Most components only support
    specific fills, so these have no purpose any more
- added `@rio.event.on_window_size_change`
- popups now default to the "hud" color
- popups and tooltips are no longer cut off by other components
- Add HTML meta tags
- Add functions for reading and writing clipboard contents to the `Session`
    (Contributed by MiniTT)
- The color of drawers is now configurable, and also sets the theme context
- added `Calendar` component
- added `DateInput` component
- massive dev-tools overhaul
- new (but experimental) `Switcher` component
- TextInputs now update their text in real-time
- `rio run` no longer opens a browser
- `rio.HTML` components now executed embedded `<script>` nodes
- added `Checkbox` Component
- `display_controls` parameter of `CodeBlock` component renamed to
    `show_controls`
- `FlowContainer` now has a convenience `spacing` parameter which controls both
    `row_spacing` and `column_spacing` at the same time

breaking:

- `Text.justify` now defaults to `"left"`
- `FlowContainer.justify` now defaults to `"left"`
- `rio.Theme` is no longer frozen, and can now be modified. This is breaking,
    because the `replace` method has been removed

## 0.8

- Rectangles now honor the theme's shadow color
- Renamed `Banner.markup` to `Banner.markdown`
- Removed the "multiline" style from Banners
- Removed `Button.initially_disabled_for`
- Added a `text_color` parameter to `Theme.from_colors` and
    `Theme.pair_from_colors`
- `rio run` now checks that the installed version of Rio is up-to-date

## 0.7

- New example: multi-page website
- New component: CodeBlock
- UserSettings can now have mutable default values
- Removed "undefined space"
