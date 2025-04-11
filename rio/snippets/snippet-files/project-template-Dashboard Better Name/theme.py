import typing as t

import rio

# Define a theme for Rio to use.
#
# You can modify the colors here to adapt the appearance of your app or website.
# The most important parameters are listed, but more are available! You can find
# them all in the docs
#
# https://rio.dev/docs/api/theme


THEME = rio.Theme.from_colors(
    mode="dark",
)

POPUP_INNER_MARGIN = 0.3
TOOLTIP_TEXTSTYLE = rio.TextStyle(font_size=0.8)

# Define brighter and darker text colors for the theme
TEXT_FILL_BRIGHTER = THEME.text_style.fill
TEXT_FILL_DARKER = THEME.text_style.fill

# Ensure that the text fill colors are of type rio.Color
# and apply the brighter and darker adjustments
assert isinstance(TEXT_FILL_BRIGHTER, rio.Color)
assert isinstance(TEXT_FILL_DARKER, rio.Color)
TEXT_FILL_BRIGHTER = TEXT_FILL_BRIGHTER.brighter(0.1)
TEXT_FILL_DARKER = TEXT_FILL_DARKER.darker(0.15)

# Define text styles for different use cases
TEXT_STYLE_DARKER_SMALL = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
    font_size=0.9,
)
TEXT_STYLE_SMALL_BOLD = rio.TextStyle(font_weight="bold", font_size=0.9)
