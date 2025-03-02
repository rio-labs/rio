# <additional-imports>
from __future__ import annotations

import rio

from . import data_models, theme
from .utils import ASSETS_DIR

# </additional-imports>

# <additional-code>
rio.Icon.register_single_icon(
    ASSETS_DIR / "discord_logo.svg",
    "thirdparty",
    "discord_logo",
)

rio.Icon.register_single_icon(
    ASSETS_DIR / "github_logo.svg",
    "thirdparty",
    "github_logo",
)


def on_session_start(sess: rio.Session) -> None:
    # Determine which layout to use
    if sess.window_width < 60:
        layout = data_models.PageLayout(
            device="mobile",
        )
    else:
        layout = data_models.PageLayout(
            device="desktop",
        )

    # Attach the layout to the session
    sess.attach(layout)


# </additional-code>


# Make sure ruff doesn't remove unused imports
# Create the Rio app
app = rio.App(
    name="Multipage Website",
    theme=theme.THEME,
)
