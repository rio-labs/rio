from __future__ import annotations

import rio

from ... import components as comps


# <component>
@rio.page(
    name="NewsPage",
    url_segment="news-page",
)
class NewsPage(rio.Component):
    """
    A sample page, containing recent news articles about the company.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("Recent News", style="heading1"),
            comps.NewsArticle(
                """
## Disruptive Innovations Inc. Unveils Game-Changing Paradigm Shift at Annual
Synergy Summit

In a move set to redefine industry standards, Disruptive Innovations Inc.
unveiled their latest groundbreaking initiative, the "Quantum Synergy Paradigm,"
at the highly anticipated Annual Synergy Summit yesterday. The event, held at
the epicenter of technological advancement, Silicon Valley, attracted a plethora
of industry thought leaders, gurus, and ninjas. Quantum Synergy Paradigm

The Quantum Synergy Paradigm promises to leverage the power of next-gen AI,
blockchain, nuclear fusion and quantum computing to create a holistic ecosystem
of perpetual growth and exponential ROI. "We are pushing the envelope to unlock
unprecedented value streams for our stakeholders," said CEO Jane Maverick, a
self-proclaimed visionary and industry disruptor. "Our mission is to catalyze a
revolution in how businesses operate, synergizing cross-functional paradigms to
achieve 110% efficiency and 200% customer satisfaction."

Attendees were treated to a spectacular holographic presentation showcasing the
paradigm's potential to integrate seamlessly with existing infrastructures,
reducing friction and maximizing scalability. Early adopters are already hailing
it as a game-changer, predicting a seismic shift in the competitive landscape.

Stay tuned as Disruptive Innovations Inc. continues to blaze trails and shatter
ceilings with their relentless pursuit of excellence and innovation.
                """
            ),
            comps.NewsArticle(
                """
## HyperTech Corp. Acquires Synergistic Solutions LLC in Unprecedented Merger of
Titans

In an unprecedented merger set to revolutionize the tech landscape, HyperTech
Corp. has acquired Synergistic Solutions LLC for a record-breaking $10 billion.
The deal, announced at a press conference brimming with buzzwords and corporate
jargon, promises to deliver unparalleled value to stakeholders and redefine the
boundaries of technological innovation. The Power of Synergy

"This merger is a quantum leap forward in our journey towards market
domination," declared HyperTech CEO John Powerhouse. "By integrating Synergistic
Solutions' disruptive capabilities with our own bleeding-edge technologies, we
are poised to create an unstoppable force of innovation and excellence. This is
not just a merger; it's a synergistic symphony of brilliance."

Synergistic Solutions, renowned for its industry-leading, blue-sky thinking and
holistic approach to problem-solving, will bring a wealth of expertise to
HyperTech's already formidable arsenal. The combined entity is expected to
accelerate the development of hyper-innovative products, leveraging
cross-functional paradigms to achieve unprecedented levels of agility and
operational efficiency.

Industry analysts are already hailing the merger as a masterstroke, predicting
it will catalyze a wave of consolidation and disruption across the tech sector.
The newly formed titan is set to embark on a relentless quest for market
supremacy, driven by a shared vision of exponential growth and unwavering
commitment to customer-centricity.

As HyperTech Corp. and Synergistic Solutions LLC join forces, the world watches
with bated breath, anticipating the dawn of a new era of technological marvels
and corporate synergies.
                """
            ),
            spacing=2,
            min_width=60,
            margin_bottom=4,
            align_x=0.5,
            align_y=0,
        )


# </component>
