# <additional-imports>
from pathlib import Path

import pandas as pd

import rio

from . import data_models, persistence

# </additional-imports>


# <additional-code>
def on_app_start(app: rio.App) -> None:
    """
    A function that runs when the app is started.
    """
    # Create a persistence instance. This class hides the gritty details of
    # database interaction from the app.
    pers = persistence.Persistence(
        csv_path=Path(__file__).parent / "assets" / "sales_data.csv",
        start_date=pd.Timestamp("2024-02-01"),
    )

    # Now attach it to the session. This way, the persistence instance is
    # available to all components using `self.session[persistence.Persistence]`
    app.default_attachments.append(pers)


def on_session_start(sess: rio.Session) -> None:
    # Determine which layout to use
    if sess.window_width < 60:
        layout = data_models.PageLayout(
            device="mobile",
            margin_app=0.5,
            margin_in_card=1,
            grow_x_content=False,
            grow_y_content=False,
        )
        # Calculate the minimum height of the content
        layout.min_width_content = (
            sess.window_width
            - 2 * layout.margin_app
            - 2 * layout.margin_in_card
        )

    else:
        layout = data_models.PageLayout(
            device="desktop",
            margin_app=4,
            margin_in_card=1,
            grow_x_content=True,
            grow_y_content=True,
        )

    # Attach the layout to the session
    sess.attach(layout)


# </additional-code>
