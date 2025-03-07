import rio

# <additional-imports>
from . import persistence

# </additional-imports>


# <additional-code>
def on_app_start(app: rio.App) -> None:
    """
    A function that runs when the app is started.
    """
    # Create a persistence instance. This class hides the gritty details of
    # database interaction from the app.
    pers = persistence.Persistence()

    # Now attach it to the session. This way, the persistence instance is
    # available to all components using `self.session[persistence.Persistence]`
    app.default_attachments.append(pers)


# </additional-code>


# <additional-demo-code>
def on_demo_session_start(sess: rio.Session) -> None:
    """
    A function that runs when a new session is started.
    """
    # Create a persistence instance.
    pers = persistence.Persistence()

    # Attach the persistence instance to the session.
    sess.attach(pers)


# </additional-demo-code>
