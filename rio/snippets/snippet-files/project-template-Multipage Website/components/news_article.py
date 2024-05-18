from __future__ import annotations

from typing import *  # type: ignore

import rio


# <component>
class NewsArticle(rio.Component):
    """
    Displays a news article with some visual separation from the background.
    """

    markdown: str

    def build(self) -> rio.Component:
        return rio.Card(
            rio.Markdown(
                self.markdown,
                margin=2,
            )
        )


# </component>
