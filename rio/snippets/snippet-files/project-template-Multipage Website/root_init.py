# <additional-imports>
from __future__ import annotations

import rio

from . import data_models
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
            # Window height, minus a little bit of extra space to have the next
            # subpage peeking through. This indicates that there's more content
            # to scroll to.
            # subpage_height=sess.window_height * 0.9,
            # center_column_width=0,
            # center_column_grow_x=True,
        )
    else:
        layout = data_models.PageLayout(
            device="desktop",
            # subpage_height=sess.window_height * 0.9,
            # # subpage_height=sess.window_height * 1.1,
            # center_column_width=60,
            # center_column_grow_x=False,
        )

    # Attach the layout to the session
    sess.attach(layout)


# </additional-code>
