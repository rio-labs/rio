import functools
import io
import typing as t

import rio


def colors_equal(color1: rio.Color, color2: rio.Color) -> bool:
    """
    Returns `True` if the two colors are equal and `False` otherwise. Since
    color values are stored as floats, this function applies a small fudge
    factor to account for floating point differences.
    """
    epsilon = 1e-6

    l1, a1, b1, opacity1 = color1.oklaba
    l2, a2, b2, opacity2 = color2.oklaba

    return (
        abs(l1 - l2) < epsilon
        and abs(a1 - a2) < epsilon
        and abs(b1 - b2) < epsilon
        and abs(opacity1 - opacity2) < epsilon
    )


def get_minimum_theme_kwargs(theme: rio.Theme) -> dict[str, t.Any]:
    """
    Given a theme, returns a dictionary with the minimum set of keyword
    arguments required to recreate it.
    """
    # This is more complex than it might seem at first, because many colors are
    # derived from other colors. For example, the neutral color is derived from
    # the primary one.
    result: dict[str, t.Any] = {}

    # Light / dark mode can impact some colors. Make sure to get that value
    # first.
    if not theme.is_light_theme:
        result["mode"] = "dark"

    # Some colors don't depend on anything else
    reference_theme = rio.Theme.from_colors(**result)

    if not colors_equal(theme.primary_color, reference_theme.primary_color):
        result["primary_color"] = theme.primary_color

    if not colors_equal(theme.secondary_color, reference_theme.secondary_color):
        result["secondary_color"] = theme.secondary_color

    if not colors_equal(theme.disabled_color, reference_theme.disabled_color):
        result["disabled_color"] = theme.disabled_color

    if not colors_equal(theme.success_color, reference_theme.success_color):
        result["success_color"] = theme.success_color

    if not colors_equal(theme.warning_color, reference_theme.warning_color):
        result["warning_color"] = theme.warning_color

    if not colors_equal(theme.danger_color, reference_theme.danger_color):
        result["danger_color"] = theme.danger_color

    if not colors_equal(theme.hud_color, reference_theme.hud_color):
        result["hud_color"] = theme.hud_color

    # These depend on the previously defined ones
    reference_theme = rio.Theme.from_colors(**result)

    if not colors_equal(
        theme.background_color, reference_theme.background_color
    ):
        result["background_color"] = theme.background_color

    if not colors_equal(theme.neutral_color, reference_theme.neutral_color):
        result["neutral_color"] = theme.neutral_color

    # Header fill
    #
    # This is nontrivial, because there are many kinds of fill, and some of them
    # can be hard to serialize. Only support solid colors for now.
    heading_color = theme.heading1_style.fill
    reference_heading_color = reference_theme.heading1_style.fill

    assert isinstance(heading_color, rio.Color), heading_color
    assert isinstance(reference_heading_color, rio.Color), (
        reference_heading_color
    )

    if isinstance(heading_color, rio.Color) and not colors_equal(
        heading_color, reference_heading_color
    ):
        result["heading_fill"] = heading_color

    # Corner radii
    if theme.corner_radius_large != reference_theme.corner_radius_large:
        result["corner_radius_large"] = theme.corner_radius_large

    if theme.corner_radius_medium != reference_theme.corner_radius_medium:
        result["corner_radius_medium"] = theme.corner_radius_medium

    if theme.corner_radius_small != reference_theme.corner_radius_small:
        result["corner_radius_small"] = theme.corner_radius_small

    return result


async def update_and_apply_theme(
    session: rio.Session,
    theme_replacements: dict[str, t.Any],
) -> None:
    """
    Overrides the session's theme with the given one, and makes sure to update
    all components so they use the new theme.
    """

    # Determine the kwargs to use for the theme
    theme_kwargs = get_minimum_theme_kwargs(session.theme)
    theme_kwargs.update(theme_replacements)

    # Build the new theme
    new_theme = rio.Theme.from_colors(**theme_kwargs)

    # Apply it
    await session._apply_theme(new_theme)


def get_source_for_theme(theme: rio.Theme, *, create_theme_pair: bool) -> str:
    """
    Given a theme, returns a string that can be used to recreate it.
    """
    # Find all parameters which must be passed to create this theme
    theme_parameters = get_minimum_theme_kwargs(theme)

    # Build the source
    theme_or_themes = "themes" if create_theme_pair else "theme"
    result = io.StringIO()
    result.write(f"# Create the {theme_or_themes}\n")

    if create_theme_pair:
        result.write("themes = rio.Theme.pair_from_colors(")
    else:
        result.write("theme = rio.Theme.from_colors(")

    if theme_parameters:
        result.write("\n")

        for key, value in theme_parameters.items():
            result.write(f"    {key}=")

            if isinstance(value, rio.Color):
                hex_value = value.hexa
                if len(hex_value) == 8 and hex_value.endswith("ff"):
                    hex_value = hex_value[:-2]

                result.write(f"rio.Color.from_hex({hex_value!r})")
            elif isinstance(value, bool):
                result.write("True" if value else "False")
            elif isinstance(value, (int, float)):
                result.write(f"{value:.2f}")
            elif isinstance(value, str):
                result.write(repr(value))
            else:
                raise NotImplementedError(f"Unsupported type: {type(value)}")

            result.write(",\n")

    result.write(")\n")
    result.write("\n")
    result.write(
        f"# And apply {'them' if create_theme_pair else 'it'} to your app\n"
    )
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
    palette_slug: str

    pick_opacity: bool = False

    round_top: bool = False
    round_bottom: bool = False

    @property
    def palette(self) -> rio.Palette:
        return getattr(self.session.theme, f"{self.palette_slug}_palette")

    async def _on_color_change(self, event: rio.ColorChangeEvent) -> None:
        await update_and_apply_theme(
            self.session,
            {
                f"{self.palette_slug}_color": event.color,
            },
        )

    def _on_press(self, event: rio.PointerEvent) -> None:
        # Toggle the popup
        if self.shared_open_key == self.palette_nicename:
            self.shared_open_key = ""
        else:
            self.shared_open_key = self.palette_nicename

    def build(self) -> rio.Component:
        palette = self.palette

        top_radius = (
            self.session.theme.corner_radius_medium if self.round_top else 0
        )
        bottom_radius = (
            self.session.theme.corner_radius_medium if self.round_bottom else 0
        )

        return rio.Popup(
            anchor=rio.PointerEventListener(
                # Switches the color of the Rectangle's ripple effect
                rio.ThemeContextSwitcher(
                    content=rio.Rectangle(
                        content=rio.Column(
                            rio.Text(
                                self.palette_nicename,
                                font_size=self.session.theme.heading3_style.font_size,
                                fill=palette.foreground,
                                selectable=False,
                                justify="left",
                            ),
                            rio.Text(
                                f"#{palette.background.hexa}",
                                font_size=1,
                                fill=palette.foreground.replace(opacity=0.5),
                                justify="left",
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
                        cursor="pointer",
                        transition_time=0.15,
                    ),
                    color=palette.background,
                ),
                on_press=self._on_press,
            ),
            content=rio.Column(
                rio.Text(
                    f"{self.palette_nicename} Color",
                    justify="center",
                    style="heading3",
                ),
                rio.ColorPicker(
                    color=palette.background,
                    pick_opacity=self.pick_opacity,
                    on_change=self._on_color_change,
                    min_width=18,
                    min_height=16,
                ),
                spacing=0.8,
                margin=1,
            ),
            is_open=self.shared_open_key == self.palette_nicename,
            color="hud",
            position="left",
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

        self.theme_variants_are_initialized = True

        current_theme_is_light = self.session.theme.is_light_theme
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

    async def _toggle_create_light_theme(
        self, _: rio.SwitchChangeEvent
    ) -> None:
        self.create_light_theme = not self.create_light_theme

        if not self.create_light_theme and not self.create_dark_theme:
            self.create_dark_theme = True

        if self.session.theme.is_light_theme and self.create_light_theme:
            theme_mode = "light"
        else:
            theme_mode = "dark"

        await update_and_apply_theme(
            self.session,
            {
                "mode": theme_mode,
            },
        )

    async def _toggle_create_dark_theme(self, _: rio.SwitchChangeEvent) -> None:
        self.create_dark_theme = not self.create_dark_theme

        if not self.create_light_theme and not self.create_dark_theme:
            self.create_light_theme = True

        if self.session.theme.is_light_theme and self.create_light_theme:
            theme_mode = "light"
        else:
            theme_mode = "dark"

        await update_and_apply_theme(
            self.session,
            {
                "mode": theme_mode,
            },
        )

    def build(self) -> rio.Component:
        # Prepare the radius sliders
        slider_min = 0
        slider_max = 4
        radius_sliders = rio.Grid(
            (
                rio.Text(
                    "Small",
                    justify="left",
                ),
                rio.Slider(
                    value=self.session.theme.corner_radius_small,
                    minimum=slider_min,
                    maximum=slider_max,
                    grow_x=True,
                    on_change=functools.partial(
                        self._on_radius_change,
                        "corner_radius_small",
                    ),
                ),
            ),
            (
                rio.Text(
                    "Medium",
                    justify="left",
                ),
                rio.Slider(
                    value=self.session.theme.corner_radius_medium,
                    minimum=slider_min,
                    maximum=slider_max,
                    grow_x=True,
                    on_change=functools.partial(
                        self._on_radius_change,
                        "corner_radius_medium",
                    ),
                ),
            ),
            (
                rio.Text(
                    "Large",
                    justify="left",
                ),
                rio.Slider(
                    value=self.session.theme.corner_radius_large,
                    minimum=slider_min,
                    maximum=slider_max,
                    grow_x=True,
                    on_change=functools.partial(
                        self._on_radius_change,
                        "corner_radius_large",
                    ),
                ),
            ),
            row_spacing=0.5,
        )

        # Combine everything
        return rio.ScrollContainer(
            rio.Column(
                # Main Colors
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Primary",
                    palette_slug="primary",
                    round_top=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Secondary",
                    palette_slug="secondary",
                    round_bottom=True,
                ),
                # Neutral Colors
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Background",
                    palette_slug="background",
                    margin_top=1,
                    round_top=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Neutral",
                    palette_slug="neutral",
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="HUD",
                    palette_slug="hud",
                    pick_opacity=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Disabled",
                    palette_slug="disabled",
                    round_bottom=True,
                ),
                # Semantic Colors
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Success",
                    palette_slug="success",
                    margin_top=1,
                    round_top=True,
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Warning",
                    palette_slug="warning",
                ),
                PalettePicker(
                    shared_open_key=self.bind().shared_open_key,
                    palette_nicename="Danger",
                    palette_slug="danger",
                    round_bottom=True,
                ),
                # Corner radii
                rio.Text(
                    "Corner Radii",
                    style="heading3",
                    margin_top=1,
                    margin_bottom=1,
                    justify="left",
                ),
                radius_sliders,
                # Theme Variants
                rio.Text(
                    "Variants",
                    style="heading3",
                    margin_top=1,
                    margin_bottom=1,
                    justify="left",
                ),
                rio.Grid(
                    [
                        rio.Text("Light Theme", justify="left"),
                        rio.Switch(
                            is_on=self.create_light_theme,
                            on_change=self._toggle_create_light_theme,
                            grow_x=True,
                        ),
                    ],
                    [
                        rio.Text("Dark Theme", justify="left"),
                        rio.Switch(
                            is_on=self.create_dark_theme,
                            on_change=self._toggle_create_dark_theme,
                            grow_x=True,
                        ),
                    ],
                    row_spacing=0.5,
                    column_spacing=0.5,
                ),
                # Code Sample
                rio.Text(
                    "Code",
                    style="heading3",
                    margin_top=1,
                    justify="left",
                ),
                rio.Text(
                    "Use this code to recreate the current theme in your app:",
                    justify="left",
                    margin_top=0.5,
                ),
                rio.CodeBlock(
                    get_source_for_theme(
                        self.session.theme,
                        create_theme_pair=self.create_light_theme
                        and self.create_dark_theme,
                    ),
                    margin_top=0.5,
                ),
                margin=1,
                align_y=0,
            ),
            scroll_x="never",
        )
