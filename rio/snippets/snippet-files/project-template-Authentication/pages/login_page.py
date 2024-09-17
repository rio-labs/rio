from __future__ import annotations

# <additional-imports>
from datetime import datetime, timezone
from typing import *  # type: ignore

import rio

from .. import components as comps
from .. import data_models, persistence

# </additional-imports>


# <component>
def guard(event: rio.GuardEvent) -> str | None:
    """
    Create a guard that checks if the user is already logged in.

    If the user is already logged in, the login page will be skipped and the user will
    be redirected to the home page.

    ## Parameters

    `event`: The event that triggered the guard containing the `session` and `active_pages`.
    """
    # If the user is already logged in, there is no reason to show the login page.

    # Is the user logged in? Fetch the `UserInformation` is logged in
    try:
        event.session[data_models.AppUser]

    except KeyError:
        return None

    # logged in, navigate to the home page
    return "/app/home"


@rio.page(name="Login", url_segment="", guard=guard)
class LoginPage(rio.Component):
    """
    Login page for accessing the website.

    This page will be used as the root component for the app. It will contain the login form
    and the sign up form. The login form consists of a username and password input field and a
    login button. The sign up form consists of a username and password input field and a sign up
    button. The sign up button will open a pop up with the sign up form when clicked.


    ## Attributes

    `username`: The username of the user.

    `password`: The password of the user.

    `error_message`: The error message to display if the login fails.

    `popup_open`: A boolean to determine if the sign up pop up is open.

    `_currently_logging_in`: A boolean to determine if the user is currently logging in.
    """

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
            await self.force_refresh()

            # Perform the login
            pers = self.session[persistence.Persistence]

            try:
                user_info = await pers.get_user_by_username(
                    username=self.username
                )
                may_login = user_info is not None and user_info.password_equals(
                    self.password
                )
                print("login accepted" if may_login else "login failed")
            except KeyError:
                may_login = False

            # If the user isn't authorized, inform them about it
            if not may_login:
                self.error_message = "Incorrect username or password. Please try again or create a new account."
                return

            # The login was successful
            assert user_info is not None
            user_info.last_login = datetime.now(timezone.utc)
            self.error_message = ""

            # Create and store a session
            user_session = await pers.create_session(
                user_id=user_info.id,
            )

            # Attach it
            self.session.attach(user_session)

            # Attach the userinfo
            self.session.attach(user_info)

            # Permanently store the session token with the connected client
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
        # create a banner with the error message if there is one
        error_banner = (
            [rio.Banner(text=self.error_message, style="danger", margin_top=1)]
            if self.error_message
            else []
        )
        return rio.Card(
            rio.Column(
                rio.Text("Login", style="heading1", justify="center"),
                # show error message if there is one
                *error_banner,
                # create the login form consisting of a username and password input field,
                # a login button and a sign up button
                rio.Row(
                    rio.Icon(
                        "material/person", min_height=3, min_width=3, align_x=1
                    ),
                    rio.TextInput(
                        text=self.bind().username,
                        label="Username",
                        # ensure the login function is called when the user presses enter
                        # on_confirm=self.login,
                        align_x=0,
                        min_width=15,
                    ),
                    spacing=0.5,
                ),
                rio.Row(
                    rio.Icon(
                        "material/lock", min_height=3, min_width=3, align_x=1
                    ),
                    rio.TextInput(
                        text=self.bind().password,
                        label="Password",
                        # Make the password field a secret field, so the password is not visible
                        # the user can make it visible by clicking on the eye icon
                        is_secret=True,
                        # ensure the login function is called when the user presses enter
                        # on_confirm=self.login,
                        align_x=0,
                        min_width=15,
                    ),
                    spacing=0.5,
                ),
                rio.Row(
                    rio.Button(
                        "Login",
                        on_press=self.login,
                        is_loading=self._currently_logging_in,
                    ),
                    # Create a sign up button that opens a pop up with a sign up form
                    # the sign up form consists of a username and password input field.
                    rio.Popup(
                        anchor=rio.Button(
                            "Sign up",
                            on_press=self.on_open_popup,
                        ),
                        content=comps.UserSignUpForm(
                            # bind popup_open to the popup_open attribute of the login page
                            # this way the popup_open attribute of the login page will be set to
                            # the value of the popup_open attribute of the sign up form when changed
                            popup_open=self.bind().popup_open,
                        ),
                        position="fullscreen",
                        is_open=self.popup_open,
                        color="primary",
                    ),
                    spacing=2,
                ),
                spacing=2,
                margin=2,
            ),
            align_x=0.5,
            align_y=0,
        )


# </component>
