import rio

from . import pages

app = rio.App(
    name="Biography",
    pages=[
        rio.Page("", pages.BiographyPage),
    ],
)


fastapi_app = app.as_fastapi()
