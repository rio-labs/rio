from __future__ import annotations

import asyncio
import dataclasses
import logging
import secrets
import typing as t
from base64 import urlsafe_b64encode
from datetime import timedelta
from hashlib import sha256

import fastapi
import timer_dict
from authlib.integrations.httpx_client import AsyncOAuth2Client

import rio

# Define constants for OAuth2 client configuration
CLIENT_ID = "..."
CLIENT_SECRET = "..."
SCOPE = "user:email"
REDIRECT_URI = "http://localhost:8001/callback"


@dataclasses.dataclass
class OAuth:
    _extension: OAuthExtension
    _session: rio.Session

    _state: t.Literal["logged-out", "logging-in", "logged-in"]

    @property
    def is_logged_in(self) -> bool:
        """
        Returns whether the client is currently authenticated.

        Returns `True` if the user has successfully been authenticated and
        `False` otherwise. This property is read-only. To log in, use the
        `login` method.

        Note that this will return `False` even if a login is currently in
        progress. You can use `is_logging_in` to check if that's the case.
        """
        return self._state == "logged-in"

    @property
    def is_logging_in(self) -> bool:
        """
        Returns whether the client is currently logging in.

        Returns `True` if the client is currently in the process of logging in
        and `False` otherwise.
        """
        return self._state == "logging-in"

    async def login(self) -> None:
        # Can't log in twice
        if self._state == "logging-in":
            raise RuntimeError("Already logging in")

        if self._state == "logged-in":
            raise RuntimeError("Already logged in")

        # Logging in now
        self._state = "logging-in"

        # Generate a code verifier and challenge for PKCE
        code_verifier = secrets.token_urlsafe(100)
        code_challenge = sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = (
            urlsafe_b64encode(code_challenge).decode("utf-8").rstrip("=")
        )

        # Create an authorization URL and state using the OAuth2 client
        async with AsyncOAuth2Client(CLIENT_ID, CLIENT_SECRET) as oauth:
            auth_url, state = oauth.create_authorization_url(
                "https://github.com/login/oauth/authorize",
                code_challenge=code_challenge,
                code_challenge_method="S256",
                redirect_uri=REDIRECT_URI,
                scope=SCOPE,  # Add scope here
            )

            # Have the user log in by redirecting to the authorization URL
            self._session.navigate_to(auth_url)

            # Wait for the callback to be received
            future = asyncio.get_event_loop().create_future()
            self._extension._pending_requests[state] = (self, future)
            code = await future

            # Create a new OAuth2 client and fetch the access token
            token = await oauth.fetch_token(
                "https://github.com/login/oauth/access_token",
                code=code,
                code_verifier=code_verifier,
                grant_type="authorization_code",
                redirect_uri=REDIRECT_URI,
            )

            # Update state
            self._state = "logged-in"

            # Fetch the user's email from GitHub
            response = await oauth.get("https://api.github.com/user")
            user_data = response.json()
            print(f"Logged in as {user_data}")

    async def logout(self) -> None:
        raise NotImplementedError("TODO")


class OAuthExtension(rio.Extension):
    """
    Easily integrate OAuth2 with Rio.

    This extension provides a simple way to authenticate users using OAuth2
    in Rio applications. It handles the OAuth2 flow, including generating the
    authorization URL, handling the callback, and fetching the access token.

    ```python
    TODO: Example usage
    ```
    """

    def __init__(self) -> None:
        # This stores currently pending authentication requests. The key is
        # the state, and the value is a tuple containing
        #
        # - The OAuth object that is waiting for the callback
        # - The future that will be set when the callback is received
        #
        # The future's parameters are the code and state received from the
        # callback.
        self._pending_requests: timer_dict.TimerDict[
            str, tuple[OAuth, asyncio.Future[str]]
        ] = timer_dict.TimerDict(
            default_duration=timedelta(minutes=5),
        )

    async def _callback_route(
        self,
        request: fastapi.Request,
    ) -> fastapi.responses.Response:
        # TODO: Come up with better responses

        # Get the code & state from the query parameters
        try:
            code = request.query_params["code"]
        except KeyError:
            logging.error(
                f"Received invalid OAuth callback. `{request.url}` did not contain a `code` query parameter."
            )
            return fastapi.responses.Response(
                content='TODO: Missing "code" query parameter',
                status_code=400,
            )

        try:
            state = request.query_params["state"]
        except KeyError:
            logging.error(
                f"Received invalid OAuth callback. `{request.url}` did not contain a `state` query parameter."
            )
            return fastapi.responses.Response(
                content='TODO: Missing "state" query parameter',
                status_code=400,
            )

        # Is an OAuth object waiting for this callback?
        try:
            oauth, future = self._pending_requests.pop(state)
        except KeyError:
            logging.error(
                f"Received invalid OAuth callback for state `{state}`. There is no pending authentication request with that state."
            )
            return fastapi.responses.Response(
                content="TODO: Invalid state",
                status_code=400,
            )

        # Update that object
        future.set_result(code)

        # Done
        return fastapi.responses.Response(
            content="TODO: You can close this tab now",
            status_code=200,
        )

    @rio.extension_event.on_as_fastapi
    def on_as_fastapi(self, event: rio.ExtensionAsFastapiEvent) -> None:
        # Add a route to handle the OAuth2 callback
        event.fastapi_app.add_api_route(
            "/callback",
            self._callback_route,
            methods=["GET"],
        )

    @rio.extension_event.on_session_start
    def on_session_start(self, event: rio.ExtensionSessionStartEvent) -> None:
        # Attach an object to the session for handling authentication
        event.session.attach(
            OAuth(
                _extension=self,
                _session=event.session,
                _state="logged-out",
            )
        )


# Define a custom component class for the root of the application
class MyRoot(rio.Component):
    logged_in_email: str | None = None

    # Asynchronous method to handle the login process
    async def on_login(self) -> None:
        # Get the OAuth object from the session
        oauth = self.session[OAuth]

        # Authenticate
        await oauth.login()

    # Method to build the UI component
    def build(self) -> rio.Component:
        if self.logged_in_email is None:
            # Display a login button if the user is not logged in
            return rio.Button(
                "Login with GitHub",
                icon="brand/github",
                on_press=self.on_login,
                align_x=0.5,
                align_y=0.5,
            )
        # Display a welcome message if the user is logged in
        return rio.Text(
            f"Hello, {self.logged_in_email}!",
            justify="center",
            align_x=0.5,
            align_y=0.5,
        )


# Create a Rio application with the custom root component
app = rio.App(
    build=MyRoot,
)


app._add_extension(OAuthExtension())
