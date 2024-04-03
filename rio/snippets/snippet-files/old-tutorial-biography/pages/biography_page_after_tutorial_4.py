from typing import *  # type: ignore

import rio

from .. import components as comps


class BiographyPage(rio.Component):
    def build(self) -> rio.Component:
        return comps.AboutMe()
