import rio

THEME = rio.theme._create_new_theme(
    mode="dark",
    # primary_color=rio.Color.from_hex("#000080"),
    background_color=rio.Color.from_hex(
        "#111827"
    ),  # Background color of the app
    neutral_color=rio.Color.from_hex(
        "#1f2937"
    ),  # Neutral color for backgrounds
    heading_fill=rio.Color.from_hex("#ffffff"),  # Fill color for headings
)

# Text on the landing page is unusually large. These constants control the
# landing page styles for it (and other things).
ACTION_TITLE_HEIGHT = 4
SUB_TITLE_HEIGHT = 2.5
ACTION_TEXT_HEIGHT = 1.05


# This scaling factor is used to reduce the size of the text on mobile
MOBILE_TEXT_SCALING = 0.75

# Image placeholder height
MOBILE_IMAGE_HEIGHT = 13

# Seperator Color
SEPERATOR_COLOR = THEME.neutral_color
NEUTRAL_COLOR_BRIGHTER = THEME.neutral_color.brighter(0.1)

# Text fill colors
TEXT_FILL_BRIGHTER = THEME.text_style.fill
TEXT_FILL_DARKER = THEME.text_style.fill
assert isinstance(TEXT_FILL_BRIGHTER, rio.Color)
assert isinstance(TEXT_FILL_DARKER, rio.Color)
TEXT_FILL_SLIGHTLY_BRIGHTER = TEXT_FILL_BRIGHTER.brighter(0.1)
TEXT_FILL_BRIGHTER = TEXT_FILL_BRIGHTER.brighter(0.5)
TEXT_FILL_DARKER = TEXT_FILL_DARKER.darker(0.2)


# General text styles
BOLD_BRIGHTER_TEXT = rio.TextStyle(
    font_weight="bold",
    fill=TEXT_FILL_BRIGHTER,
)

DARKER_TEXT = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
)
DARK_TEXT_BIGGER = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
    font_size=1.1,
)
DARK_TEXT_SMALLER = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
    font_size=0.9,
)


# Text style for desktop
BOLD_BIGGER_SECTION_TITEL_DESKTOP = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * 1.1,
    font_weight="bold",
)


BOLD_SECTION_TITEL_DESKTOP = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT,
    font_weight="bold",
)

BOLD_SMALLER_SECTION_TITEL_DESKTOP = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * 0.8,
    font_weight="bold",
)


# Text style for mobile
BOLD_BIGGER_SECTION_TITEL_MOBILE = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * 1.1 * MOBILE_TEXT_SCALING,
    font_weight="bold",
)

BOLD_SECTION_TITEL_MOBILE = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * MOBILE_TEXT_SCALING,
    font_weight="bold",
)


BOLD_SMALLER_SECTION_TITLE_MOBILE = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=ACTION_TITLE_HEIGHT * MOBILE_TEXT_SCALING,
    font_weight="bold",
)
