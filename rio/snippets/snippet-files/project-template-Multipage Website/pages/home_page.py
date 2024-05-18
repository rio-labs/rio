from __future__ import annotations

from typing import *  # type: ignore

import rio

from .. import components as comps


# <component>
class HomePage(rio.Component):
    """
    A sample page, containing a greeting and some testimonials.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Markdown(
                """
# Buzzwordz Inc.!

Unleashing synergistic paradigms for unprecedented excellence since the day
after yesterday.
            """,
                width=60,
                align_x=0.5,
            ),
            rio.Row(
                comps.Testimonial(
                    "Disruptive Innovations Inc. is the vanguard of operational excellence and groundbreaking innovation.",
                    "Jane Doe",
                    "CTO, Synergistic Solutions LLC",
                ),
                comps.Testimonial(
                    "They blew my socks off, and I wasn't even wearing any!",
                    "Made Up Rick",
                    "CEO, Imaginary Industries",
                ),
                comps.Testimonial(
                    "The Quantum Synergy Paradigm is a game-changer! I've never seen anything like it.",
                    "John Doe",
                    "CEO, HyperTech Corp.",
                ),
                spacing=2,
                align_x=0.5,
            ),
            rio.Markdown(
                """
Contact us today to unlock your business's quantum potential and embark on a
journey of transformational growth and stratospheric success.
            """,
                width=60,
                align_x=0.5,
            ),
            spacing=2,
            width=60,
            align_x=0.5,
            align_y=0,
        )


# </component>
