from __future__ import annotations

from typing import *  # type: ignore

import rio

from . import components as comps
from . import pages

app = rio.App(
    name="Rio",
    icon=rio.common.RIO_LOGO_ASSET_PATH,
    pages=[
        rio.Page(
            page_url="",
            build=pages.Dashboard,
        ),
    ],
    theme=rio.Theme.from_color(),
)
