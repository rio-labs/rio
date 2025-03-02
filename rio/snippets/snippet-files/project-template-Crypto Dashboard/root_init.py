import rio

# <additional-imports>
from . import data_models, theme

# </additional-imports>


# <additional-code>
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
    name="crypto_dashboard",
    theme=theme.THEME,
)
