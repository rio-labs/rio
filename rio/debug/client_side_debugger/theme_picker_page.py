import functools
import io
from typing import *  # type: ignore

import rio


async def update_and_apply_theme(
    session: rio.Session,
    theme_replacements: dict[str, Any],
) -> None:
    """
    Overrides the session's theme with the given one, and makes sure to update
    all components so they use the new theme.
    """

    # Build the new theme
    updated_theme = session.theme.replace(**theme_replacements)

    # The theme theme itself can preserve some values. For example, the primary
    # color is encoded in the heading text style, so just replacing the primary
    # palette won't make it go away.
    #
    # When passing the values, make sure to only change those that have been
    # changed relative to the default,
    #
    # Take care of that.
    new_theme = rio.Theme.from_color(
        primary_color=updated_theme.primary_color,
        secondary_color=updated_theme.secondary_color,
        background_color=updated_theme.background_color,
        neutral_color=updated_theme.neutral_color,
        hud_color=updated_theme.hud_color,
        disabled_color=updated_theme.disabled_color,
        success_color=updated_theme.success_color,
        warning_color=updated_theme.warning_color,
        danger_color=updated_theme.danger_color,
        corner_radius_small=updated_theme.corner_radius_small,
        corner_radius_medium=updated_theme.corner_radius_medium,
        corner_radius_large=updated_theme.corner_radius_large,
        color_headings="auto",  # TODO: How to decide this?
        light=updated_theme.background_color.perceived_brightness > 0.5,
    )

    # Apply the theme
    await session._apply_theme(new_theme)

    # The application itself isn't enough, because some components will have
    # read theme values and used them to set e.g. their corner radii. Dirty
    # every component to force a full rebuild.
    for component in session._weak_components_by_id.values():
        session._register_dirty_component(
            component,
            include_children_recursively=False,
        )

    # Refresh
    await session._refresh()


def get_source_for_theme(theme: rio.Theme, *, create_theme_pair: bool) -> str:
    """
    Given a theme, returns a string that can be used to recreate it.
    """
    # Find all values that differ from the defaults
    default_theme = rio.Theme.from_color()
    changed_kwargs = {}

    if theme.primary_color != default_theme.primary_color:
        changed_kwargs["primary_color"] = theme.primary_color

    if theme.secondary_color != default_theme.secondary_color:
        changed_kwargs["secondary_color"] = theme.secondary_color

    if theme.background_color != default_theme.background_color:
        changed_kwargs["background_color"] = theme.background_color

    if theme.neutral_color != default_theme.neutral_color:
        changed_kwargs["neutral_color"] = theme.neutral_color

    if theme.hud_color != default_theme.hud_color:
        changed_kwargs["hud_color"] = theme.hud_color

    if theme.disabled_color != default_theme.disabled_color:
        changed_kwargs["disabled_color"] = theme.disabled_color

    if theme.success_color != default_theme.success_color:
        changed_kwargs["success_color"] = theme.success_color

    if theme.warning_color != default_theme.warning_color:
        changed_kwargs["warning_color"] = theme.warning_color

    if theme.danger_color != default_theme.danger_color:
        changed_kwargs["danger_color"] = theme.danger_color

    if theme.corner_radius_small != default_theme.corner_radius_small:
        changed_kwargs["corner_radius_small"] = round(theme.corner_radius_small, 1)

    if theme.corner_radius_medium != default_theme.corner_radius_medium:
        changed_kwargs["corner_radius_medium"] = round(theme.corner_radius_medium, 1)

    if theme.corner_radius_large != default_theme.corner_radius_large:
        changed_kwargs["corner_radius_large"] = round(theme.corner_radius_large, 1)

    if theme.neutral_color.perceived_brightness < 0.5:
        changed_kwargs["light"] = False

    # Build the source
    theme_or_themes = "themes" if create_theme_pair else "theme"
    result = io.StringIO()
    result.write(f"# Create the {theme_or_themes}\n")

    if create_theme_pair:
        result.write("themes = rio.Theme.pair_from_color(")
    else:
        result.write("theme = rio.Theme.from_color(")

    if changed_kwargs:
        result.write("\n")

        for key, value in changed_kwargs.items():
            result.write(f"    {key}=")

            if isinstance(value, rio.Color):
                hex_value = value.hex
                if len(hex_value) == 8 and hex_value.endswith("ff"):
                    hex_value = hex_value[:-2]

                result.write(f"rio.Color.from_hex({hex_value!r})")
            elif isinstance(value, (int, float)):
                result.write(repr(value))
            else:
                raise NotImplementedError(f"Unsupported type: {type(value)}")

            result.write(",\n")

    result.write(")\n")
    result.write("\n")
    result.write(f"# And apply {'them' if create_theme_pair else 'it'} to your app\n")
    result.write("app = rio.App(\n")
    result.write("    ...\n")
    result.write(f"    theme={theme_or_themes},\n")
    result.write("    ...\n")
    result.write(")")

    # Done
    return result.getvalue()


class PalettePicker(rio.Component):  #
    shared_open_key: str

    palette_nicename: str
    palette_attribute_name: str

    is_colorful_palette: bool

    pick_opacity: bool = False

    round_top: bool = False
    round_bottom: bool = False

    @property
    def palette(self) -> rio.Palette:
        return getattr(self.session.theme, self.palette_attribute_name)

    async def _on_color_change(self, event: rio.ColorChangeEvent) -> None:
        await update_and_apply_theme(
            self.session,
            {
                self.palette_attribute_name: rio.Palette._from_color(
                    event.color,
                    colorful=self.is_colorful_palette,
                )
            },
        )

    def _on_press(self, event: rio.PressEvent) -> None:
        # Toggle the popup
        if self.shared_open_key == self.palette_nicename:
            self.shared_open_key = ""
        else:
            self.shared_open_key = self.palette_nicename

    def build(self) -> rio.Component:
        palette = self.palette

        top_radius = self.session.theme.corner_radius_medium if self.round_top else 0
        bottom_radius = (
            self.session.theme.corner_radius_medium if self.round_bottom else 0
        )

        return rio.Popup(
            anchor=rio.MouseEventListener(
                rio.Rectangle(
                    content=rio.Column(
                        rio.Text(
                            self.palette_nicename,
                            style=rio.TextStyle(
                                # font_size=self.session.theme.heading3_style.font_size,
                                fill=palette.foreground,
                            ),
                            selectable=False,
                            align_x=0,
                        ),
                        rio.Text(
                            f"#{palette.background.hex}",
                            style=rio.TextStyle(
                                font_size=1,
                                fill=palette.foreground.replace(opacity=0.5),
                            ),
                            align_x=0,
                        ),
                        spacing=0.2,
                        margin_x=1,
                        margin_y=0.8,
                    ),
                    fill=palette.background,
                    corner_radius=(
                        top_radius,
                        top_radius,
                        bottom_radius,
                        bottom_radius,
                    ),
                    ripple=True,
                    transition_time=0.15,
                ),
                on_press=self._on_press,
            ),
            content=rio.Column(
                rio.Text(
                    f"{self.palette_nicename} Color",
                    style="heading3",
                ),
                rio.ColorPicker(
                    color=palette.background,
                    pick_opacity=self.pick_opacity,
                    on_change=self._on_color_change,
                    width=18,
                    height=16,
                ),
                spacing=0.8,
                margin=1,
            ),
            is_open=self.shared_open_key == self.palette_nicename,
            color="hud",
            direction="left",
            gap=1,
        )


class ThemePickerPage(rio.Component):
    shared_open_key: str = ""

    theme_variants_are_initialized: bool = False
    create_light_theme: bool = True
    create_dark_theme: bool = False

    @rio.event.on_populate
    async def _on_populate(self) -> None:
        if self.theme_variants_are_initialized:
            return

        current_theme_is_light = (
            self.session.theme.background_color.perceived_brightness > 0.5
        )

        self.create_light_theme = current_theme_is_light
        self.create_dark_theme = not current_theme_is_light

    async def _on_radius_change(
        self,
        radius_name: str,
        event: rio.SliderChangeEvent,
    ) -> None:
        await update_and_apply_theme(
            self.session,
            {
                radius_name: event.value,
            },
        )

    def _toggle_create_light_theme(self) -> None:
        self.create_light_theme = not self.create_light_theme

        if not self.create_light_theme and not self.create_dark_theme:
            self.create_dark_theme = True

    def _toggle_create_dark_theme(self) -> None:
        self.create_dark_theme = not self.create_dark_theme

        if not self.create_light_theme and not self.create_dark_theme:
            self.create_light_theme = True

    def build(self) -> rio.Component:
        # Prepare the radius sliders
        slider_min = 0
        slider_max = 4
        radius_sliders = rio.Grid(
            (
                rio.Text("Small"),
                rio.Slider(
                    value=self.session.theme.corner_radius_small,
                    minimum=slider_min,
                    maximum=slider_max,
                    width="grow",
                    on_change=functools.partial(
                        self._on_radius_change,
                        "corner_radius_small",
                    ),
                ),
            ),
            (
                rio.Text("Medium"),
                rio.Slider(
                    value=self.session.theme.corner_radius_medium,
                    minimum=slider_min,
                    maximum=slider_max,
                    width="grow",
                    on_change=functools.partial(
                        self._on_radius_change,
                        "corner_radius_medium",
                    ),
                ),
            ),
            (
                rio.Text("Large"),
                rio.Slider(
                    value=self.session.theme.corner_radius_large,
                    minimum=slider_min,
                    maximum=slider_max,
                    width="grow",
                    on_change=functools.partial(
                        self._on_radius_change,
                        "corner_radius_large",
                    ),
                ),
            ),
        )

        # Combine everything
        return rio.ScrollContainer(
            content=rio.Column(
                # Main Colors
                # rio.Text(
                #     "Theme Colors",
                #     style="heading3",
                #     margin_bottom=1,
                #     align_x=0,
                # ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Primary",
                    palette_attribute_name="primary_palette",
                    is_colorful_palette=False,
                    round_top=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Secondary",
                    palette_attribute_name="secondary_palette",
                    is_colorful_palette=False,
                    round_bottom=True,
                ),
                # Neutral Colors
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Background",
                    palette_attribute_name="background_palette",
                    is_colorful_palette=False,
                    margin_top=1,
                    round_top=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Neutral",
                    palette_attribute_name="neutral_palette",
                    is_colorful_palette=False,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="HUD",
                    palette_attribute_name="hud_palette",
                    is_colorful_palette=False,
                    pick_opacity=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Disabled",
                    palette_attribute_name="disabled_palette",
                    is_colorful_palette=False,
                    round_bottom=True,
                ),
                # Semantic Colors
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Success",
                    palette_attribute_name="success_palette",
                    is_colorful_palette=True,
                    margin_top=1,
                    round_top=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Warning",
                    palette_attribute_name="warning_palette",
                    is_colorful_palette=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Danger",
                    palette_attribute_name="danger_palette",
                    is_colorful_palette=True,
                    round_bottom=True,
                ),
                # Corner radii
                rio.Text(
                    "Corner Radii",
                    style="heading3",
                    margin_top=1,
                    margin_bottom=1,
                    align_x=0,
                ),
                radius_sliders,
                # Theme Variants
                rio.Text(
                    "Theme Variants",
                    style="heading3",
                    margin_top=1,
                    margin_bottom=1,
                    align_x=0,
                ),
                rio.Row(
                    rio.Spacer(),
                    rio.IconButton(
                        "material/light-mode",
                        style="minor" if self.create_light_theme else "plain",
                        on_press=self._toggle_create_light_theme,
                    ),
                    rio.Spacer(),
                    rio.IconButton(
                        "material/dark-mode",
                        style="minor" if self.create_dark_theme else "plain",
                        on_press=self._toggle_create_dark_theme,
                    ),
                    rio.Spacer(),
                ),
                # Code Sample
                rio.Text(
                    "Code Sample",
                    style="heading3",
                    margin_top=1,
                    # margin_bottom=1,  Not used for now, since markdown has an oddly large margin anyway
                    align_x=0,
                ),
                rio.Markdown(
                    f"""
```python
{get_source_for_theme(self.session.theme, create_theme_pair=self.create_light_theme and self.create_dark_theme)}
```
                    """,
                ),
                margin=1,
                align_y=0,
            ),
            scroll_x="never",
        )
