import dataclasses
import functools
import re
from dataclasses import KW_ONLY
from typing import *  # type: ignore

import fuzzywuzzy.fuzz

import rio
import rio.icon_registry

from . import sample_icons_grid

T = TypeVar("T")


# Replace all sequences non-alphanumeric characters with a single dot
NORMALIZATION_PATTERN = re.compile(r"[^a-zA-Z0-9]+")

# Cache for all icons known to Rio. Finding the icons requires file system
# access and is slow - this caches them.
#
# The entires are (icon_set, icon_name, {variant_name}) tuples. The variant name
# is a set of all variants that exist for this icon.
ALL_AVAILABLE_ICONS: list[tuple[str, str, tuple[str | None, ...]]] | None = None


def normalize_for_search(text: str) -> str:
    """
    Normalize a string for search, making search more forgiving.
    """
    text = NORMALIZATION_PATTERN.sub(".", text)
    text = text.strip(".")
    text = text.lower()
    return text


def search(
    needle: str,
    haystack: list[T],
    *,
    min_results: int = 5,
    threshold: float = 0.85,
    key: Callable[[T], str] = lambda x: x,  # type: ignore
) -> list[tuple[T, float]]:
    """
    Given a set of candidate strings, return the best matches for the provided
    search string. The result is a list of (string, score) tuples, sorted by
    score. The score is 1.0 for a perfect match and 0.0 for no match.
    """
    # Convert the haystack elements to strings using the provided key function
    haystack_strs = [key(item) for item in haystack]

    # Use fuzzywuzzy to get the matches and their scores
    scores = [
        fuzzywuzzy.fuzz.partial_ratio(needle, haystack_strs)
        for haystack_strs in haystack_strs
    ]

    # Sort the original values by their score
    scored_haystack = sorted(
        zip(haystack, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    # Apply a threshold, but never remove all results
    result = []
    for ii, (item, score) in enumerate(scored_haystack):
        score = score / 100

        if score < threshold and ii >= min_results:
            break

        result.append((item, score))

    return result


def get_available_icons() -> list[tuple[str, str, tuple[str | None, ...]]]:
    """
    Return a list of all available icons. The result is cached, so subsequent
    calls are fast.

    The result is a list of tuples (icon_set, icon_name, {variant_names}).
    """
    global ALL_AVAILABLE_ICONS

    # Cached?
    if ALL_AVAILABLE_ICONS is not None:
        return ALL_AVAILABLE_ICONS

    # Nope, get to work. Iterate over all icons and variants and group them.
    registry = rio.icon_registry.IconRegistry.get_singleton()
    result_dict: dict[str, tuple[str, str, set[str | None]]] = {}

    for icon_set in registry.all_icon_sets():
        for icon_name, variant_name in registry.all_icons_in_set(icon_set):
            key = f"{icon_set}/{icon_name}"

            try:
                _, _, variants = result_dict[key]
            except KeyError:
                variants = {variant_name}
                result_dict[key] = (icon_set, icon_name, variants)
            else:
                variants.add(variant_name)

    # Drop the dict
    as_list: list[Any] = list(result_dict.values())

    # Sort the result
    as_list.sort(key=lambda x: x[1])

    for ii, (icon_set, icon_name, variants) in enumerate(as_list):
        variants = tuple(sorted(variants, key=lambda x: "" if x is None else x))
        as_list[ii] = (icon_set, icon_name, variants)

    # Cache and return
    ALL_AVAILABLE_ICONS = as_list  # type: ignore
    return ALL_AVAILABLE_ICONS  # type: ignore


class IconsPage(rio.Component):
    _: KW_ONLY
    search_text: str = ""
    matches: list[tuple[str, str, tuple[str | None, ...]]] = dataclasses.field(
        default_factory=list
    )

    selected_icon: str | None = (
        None  # The selected icon, **including the icon set**
    )
    selected_icon_available_variants: tuple[str | None, ...] = (
        dataclasses.field(default_factory=tuple)
    )
    selected_variant: str | None = None
    selected_fill: Literal[
        "primary",
        "secondary",
        "success",
        "warning",
        "danger",
        "keep",
        "dim",
    ] = "keep"

    def _on_search_text_change(self, *_) -> None:
        # No search -> no matches
        self.matches = []
        normalized_search_text = self.search_text.strip()

        if not normalized_search_text:
            return

        # TODO: Add a proper search
        scored_matches = search(
            normalized_search_text,
            get_available_icons(),
            key=lambda x: x[1],
        )

        self.matches = [x for x, _ in scored_matches]

    async def _on_select_icon_by_name(self, icon_name: str) -> None:
        # Parse the icon name
        (
            icon_set,
            icon_name,
            icon_variant,
        ) = rio.icon_registry.IconRegistry.parse_icon_name(icon_name)

        # Find all available variants
        for (
            other_icon_set,
            other_icon_name,
            available_variants,
        ) in get_available_icons():
            if icon_name == other_icon_name and icon_set == other_icon_set:
                break
        else:
            assert False, f"There is no icon named `{icon_name}` in the `{icon_set}` icon set"

        # Delegate to the regular function for this
        self._on_select_icon(icon_set, icon_name, available_variants)

        # Set any state that wasn't handled by the previous call
        self.search_text = icon_name
        self.selected_variant = icon_variant

        self._on_search_text_change()

    def _on_select_icon(
        self,
        icon_set: str,
        icon_name: str,
        available_variants: tuple[str | None, ...],
    ) -> None:
        self.selected_icon = icon_set + "/" + icon_name
        self.selected_variant = available_variants[0]
        self.selected_icon_available_variants = available_variants

    def _on_select_variant(self, variant: str | None) -> None:
        self.selected_variant = variant

    def build_details(self) -> rio.Component:
        assert self.selected_icon is not None
        children = []

        # Heading
        children.append(
            rio.Text(
                "Configure",
                style="heading3",
                justify="left",
            )
        )

        # Fill
        children.append(
            rio.Dropdown(
                label="Fill",
                options=[
                    "primary",
                    "secondary",
                    "success",
                    "warning",
                    "danger",
                    "keep",
                    "dim",
                ],
                selected_value=self.bind().selected_fill,
            )
        )

        # If there is variations of this icon allow the user to select one
        # if len(self.selected_icon_available_variants) > 1:
        if True:
            variant_buttons = []

            for variant in self.selected_icon_available_variants:
                full_name = (
                    f"{self.selected_icon}:{variant}"
                    if variant
                    else self.selected_icon
                )

                if self.selected_fill == "dim":
                    color = (
                        self.session.theme.neutral_palette.foreground.replace(
                            opacity=0.5
                        )
                    )
                else:
                    color = self.selected_fill

                variant_buttons.append(
                    rio.Container(
                        rio.IconButton(
                            full_name,
                            style=(
                                "minor"
                                if variant == self.selected_variant
                                else "plain"
                            ),
                            color=color,
                            on_press=functools.partial(
                                self._on_select_variant, variant
                            ),
                        ),
                        width="grow",
                        align_y=0.5,
                    )
                )

            children.append(rio.Row(*variant_buttons, width="grow"))

        # Which parameters should be passed?
        params_dict = {
            "width": "2.5",
            "height": "2.5",
        }

        if self.selected_fill != "keep":
            params_dict["fill"] = repr(self.selected_fill)

        # Prepare the source code
        selected_icon_full_name = self.selected_icon + (
            "" if self.selected_variant is None else ":" + self.selected_variant
        )

        params_list = [repr(selected_icon_full_name)] + [
            f"{key}={value}" for key, value in params_dict.items()
        ]

        params_str = ",\n    ".join(params_list)
        python_source = f"rio.Icon(\n    {params_str},\n)"

        # Code sample
        children.append(
            rio.Text(
                "Example Code",
                style="heading3",
                justify="left",
                margin_top=1,
            )
        )

        children.append(
            rio.Markdown(
                f"""
Use the `rio.Icon` component like this:

```python
{python_source}
```
"""
            )
        )

        # Combine everything
        return rio.Column(*children, spacing=0.8)

    def build(self) -> rio.Component:
        children: list[rio.Component] = []
        has_search = bool(self.search_text)

        # Top Decoration
        if not has_search:
            children.append(
                rio.Text(
                    "Rio comes with a large array of icons out of the box. You can find them all here.",
                    wrap=True,
                    style=rio.TextStyle(
                        font_size=1.1,
                        font_weight="bold",
                        fill=self.session.theme.secondary_color,
                    ),
                    margin_bottom=1,
                )
            )

        # Search field
        children.append(
            rio.TextInput(
                label="Search for an icon",
                text=self.bind().search_text,
                on_change=self._on_search_text_change,
            ),
        )

        # Display the top results in a grid
        if self.matches:
            results = []

            for icon_set, icon_name, icon_variants in self.matches[:50]:
                is_selected = self.selected_icon == f"{icon_set}/{icon_name}"

                results.append(
                    rio.IconButton(
                        f"{icon_set}/{icon_name}",
                        style="minor" if is_selected else "plain",
                        on_press=functools.partial(
                            self._on_select_icon,
                            icon_set,
                            icon_name,
                            icon_variants,
                        ),
                        key=f"{icon_set}/{icon_name}",
                    ),
                )

            children.append(
                rio.FlowContainer(
                    *results,
                    row_spacing=0.5,
                    column_spacing=0.5,
                    justify="left",
                    height="grow",
                    align_y=0,
                )
            )

        # Bottom Decoration
        if not has_search:
            children.append(
                sample_icons_grid.SampleIconsGrid(
                    height="grow",
                    margin_top=2,
                    on_select_icon=self._on_select_icon_by_name,
                )
            )

        # No results
        if has_search and not self.matches:
            children.append(
                rio.Container(
                    rio.Column(
                        rio.Icon(
                            "material/search",
                            width=4,
                            height=4,
                            fill="dim",
                            align_x=0.5,
                        ),
                        rio.Text(
                            "No results",
                            style="dim",
                        ),
                        spacing=1,
                        align_y=0.5,
                    ),
                    height="grow",
                )
            )

        # If an icon is selected, show its details
        if has_search and self.selected_icon is not None:
            children.append(self.build_details())

        # Combine everything
        return rio.ScrollContainer(
            rio.Column(
                *children,
                spacing=1,
                margin=1,
            ),
            scroll_x="never",
        )
