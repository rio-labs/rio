import rio

from .. import data_models as data_models

# <additional-imports>
from .. import persistence

# </additional-imports>


# <component>
class UserSignUpForm(rio.Component):
    """
    Provides interface for users to sign up for a new account.

    It includes fields for username and password, handles user creation, and displays error messages
    if the sign-up process fails.

    ## Attributes

    `popup_open`: A boolean to determine if the sign up pop up is open.

    `username_sign_up`: The username of the user.

    `password_sign_up`: The password of the user.

    `password_sign_up_repeat`: The repeated password of the user.

    `error_message_sign_up`: The error message to display if the sign up fails.

    `username_valid`: A boolean to determine if the username is valid.

    `passwords_valid`: A boolean to determine if the passwords are valid.
    """

    popup_open: bool

    username_sign_up: str = ""
    password_sign_up: str = ""
    password_sign_up_repeat: str = ""

    error_message_sign_up: str = ""

    username_valid: bool = True
    passwords_valid: bool = True

    async def on_sign_up(self) -> None:
        """
        Handles the sign-up process when the user submits the sign-up form.

        It will check if the user already exists and if the passwords match. If the user does not
        exist and the passwords match, a new user will be created and stored in the database.
        """
        pers = self.session[persistence.Persistence]

        # Check if username and passwords are empty
        if (
            not self.username_sign_up
            or not self.password_sign_up
            or not self.password_sign_up_repeat
        ):
            self.error_message_sign_up = "Please fill in all fields"
            self.passwords_valid = False
            self.username_valid = False
            return

        # Check if the passwords match
        if self.password_sign_up != self.password_sign_up_repeat:
            self.error_message_sign_up = "Passwords do not match"
            # Signaling that the password is invalid
            self.passwords_valid = False
            self.username_valid = True
            return

        # check if user already exists
        if await pers.get_user_by_username(username=self.username_sign_up):
            self.error_message_sign_up = "User already exists"
            # Signaling that the username is invalid
            self.username_valid = False
            self.passwords_valid = True
            return

        # Create a new user
        user_info = data_models.LoggedInUser.new_with_defaults(
            username=self.username_sign_up,
            password=self.password_sign_up,
        )

        # Store the user in the database
        await pers.add_user(user_info)
        print(f"User info: {user_info}")
        print("user added")

        # close pop up
        self.popup_open = False

    def on_cancel(self) -> None:
        """
        Closes the sign-up popup when the user clicks the cancel button.

        It also resets all fields to their default values.
        """
        # set all fields to default values
        self.username_valid: bool = True
        self.passwords_valid: bool = True
        self.username_sign_up: str = ""
        self.password_sign_up: str = ""
        self.password_sign_up_repeat: str = ""
        self.error_message_sign_up: str = ""

        # close pop up
        self.popup_open = False

    def build(self) -> rio.Component:
        error_banner_sign_up = (
            [
                rio.Banner(
                    text=self.error_message_sign_up,
                    style="danger",
                    margin_top=1,
                )
            ]
            if self.error_message_sign_up
            else []
        )

        return rio.Card(
            rio.Column(
                rio.Text("Create a new account", style="heading1"),
                *error_banner_sign_up,
                rio.Row(
                    rio.Icon(
                        "material/person", min_height=3, min_width=3, align_x=1
                    ),
                    rio.TextInput(
                        text=self.bind().username_sign_up,
                        label="Username*",
                        is_valid=self.username_valid,
                        align_x=0,
                        grow_x=True,
                        min_width=20,
                    ),
                ),
                rio.Row(
                    rio.Icon(
                        "material/lock", min_height=3, min_width=3, align_x=1
                    ),
                    rio.TextInput(
                        text=self.bind().password_sign_up,
                        label="Password*",
                        is_valid=self.passwords_valid,
                        align_x=0,
                        grow_x=True,
                        min_width=20,
                    ),
                ),
                rio.Row(
                    rio.Icon(
                        "material/lock", min_height=3, min_width=3, align_x=1
                    ),
                    rio.TextInput(
                        text=self.bind().password_sign_up_repeat,
                        label="Repeat Password*",
                        is_valid=self.passwords_valid,
                        align_x=0,
                        grow_x=True,
                        min_width=20,
                    ),
                ),
                rio.Row(
                    rio.Button(
                        "Sign up",
                        on_press=self.on_sign_up,
                    ),
                    rio.Button(
                        "Cancel",
                        on_press=self.on_cancel,
                    ),
                    spacing=2,
                ),
                spacing=2,
                margin=2,
            ),
            align_x=0.5,
            align_y=0.5,
        )


# </component>
