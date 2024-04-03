from dataclasses import KW_ONLY
from typing import *  # type: ignore

import rio


class Contact(rio.Component):
    text: str
    icon_name_or_url: str | rio.URL
    _: KW_ONLY
    link: rio.URL | None = None

    def build(self) -> rio.Component:
        # Prepare the image. This varies depending on whether an icon or an
        # image should be displayed.
        if isinstance(self.icon_name_or_url, str):
            image = rio.Icon(
                self.icon_name_or_url,
                width=2,
                height=2,
                margin_x=0.5,
            )
        else:
            image = rio.Image(
                self.icon_name_or_url,
                width=2,
                height=2,
                margin_x=0.5,
            )

        # Combine everything
        result = rio.Row(
            image,
            rio.Text(
                self.text,
                align_x=0,
                width="grow",
            ),
            width="grow",
            margin=0.2,
        )

        # If a link is provided, wrap the result in a link
        if self.link is not None:
            result = rio.Link(
                result,
                self.link,
            )

        return result
