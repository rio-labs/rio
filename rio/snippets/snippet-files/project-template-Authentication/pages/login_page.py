from __future__ import annotations

# <additional-imports>
import rio

from .. import components as comps
from .. import data_models, persistence

# </additional-imports>


# <component>
def guard(event: rio.GuardEvent) -> str | None:
    """
    A guard which only allows the user to access this page if they are not
    logged in yet. If the user is already logged in, the login page will be
    skipped and the user will be redirected to the home page instead.
    """
    # Check if the user is authenticated by looking for a user session
    try:
        event.session[data_models.AppUser]

    # User is not logged in, no redirection needed
    except KeyError:
        return None

    # User is logged in, redirect to the home page
    return "/app/home"


@rio.page(
    name="Login",
    url_segment="",
    guard=guard,
)
class LoginPage(rio.Component):
    """
    Login page for accessing the website.
    """

    # These are used to store the currently entered values from the user
    username: str = ""
    password: str = ""

    error_message: str = ""
    popup_open: bool = False

    _currently_logging_in: bool = False

    async def login(self, _: rio.TextInputConfirmEvent | None = None) -> None:
        """
        Handles the login process when the user submits their credentials.

        It will check if the user exists and if the password is correct. If the
        user exists and the password is correct, the user will be logged in and
        redirected to the home page.
        """
        try:
            # Inform the user that something is happening
            self._currently_logging_in = True
            self.force_refresh()

            #  Try to find a user with this name
            pers = self.session[persistence.Persistence]

            try:
                user_info = await pers.get_user_by_username(
                    username=self.username
                )
            except KeyError:
                self.error_message = "Invalid username. Please try again or create a new account."
                return

            # Make sure their password matches
            if not user_info.password_equals(self.password):
                self.error_message = "Invalid password. Please try again or create a new account."
                return

            # The login was successful
            self.error_message = ""

            # Create and store a session
            user_session = await pers.create_session(
                user_id=user_info.id,
            )

            # Attach the session and userinfo. This indicates to any other
            # component in the app that somebody is logged in, and who that is.
            self.session.attach(user_session)
            self.session.attach(user_info)

            # Permanently store the session token with the connected client.
            # This way they can be recognized again should they reconnect later.
            settings = self.session[data_models.UserSettings]
            settings.auth_token = user_session.id
            self.session.attach(settings)

            # The user is logged in - no reason to stay here
            self.session.navigate_to("/app/home")

        # Done
        finally:
            self._currently_logging_in = False

    def on_open_popup(self) -> None:
        """
        Opens the sign-up popup when the user clicks the sign-up button
        """
        self.popup_open = True

    def build(self) -> rio.Component:
        # Determine the layout based on the window width
        desktop_layout = self.session.window_width > 30

        return rio.Card(
            rio.Column(
                rio.Text("Sign In", style="heading1", justify="center"),
                # Show error message if there is one
                #
                # Banners automatically appear invisible if they don't have
                # anything to show, so there is no need for a check here.
                rio.Banner(
                    text=self.error_message,
                    style="danger",
                    margin_top=1,
                ),
                # Create the login form consisting of a username and password
                # input field, a login button and a sign up button
                rio.TextInput(
                    text=self.bind().username,
                    label="Username",
                    # ensure the login function is called when the user presses enter
                    on_confirm=self.login,
                ),
                rio.TextInput(
                    text=self.bind().password,
                    label="Password",
                    # Mark the password field as secret so the password is
                    # hidden while typing
                    is_secret=True,
                    # Ensure the login function is called when the user presses
                    # enter
                    on_confirm=self.login,
                ),
                rio.Button(
                    "Sign In",
                    on_press=self.login,
                    is_loading=self._currently_logging_in,
                ),
                # Create a sign up button that opens a pop up with a sign up
                # form
                rio.Popup(
                    anchor=rio.Button(
                        "Create an Account",
                        on_press=self.on_open_popup,
                        style="minor",
                    ),
                    content=comps.UserSignUpForm(
                        # Bind `popup_open` to the `popup_open` attribute of
                        # the login page. This way the page's attribute will
                        # always have the same value as that of the form,
                        # even when one changes.
                        popup_open=self.bind().popup_open,
                    ),
                    position="fullscreen",
                    is_open=self.popup_open,
                    color="none",
                ),
                spacing=1,
                margin=2 if desktop_layout else 1,
            ),
            margin_x=0.5,
            align_y=0.5,
            align_x=0.5 if desktop_layout else None,
            min_width=24 if desktop_layout else 0,
        )


# </component>
