from datetime import timedelta
from typing import *  # type: ignore

import httpx

BASE_URL = "https://rio.dev/api"


class ApiException(Exception):
    """
    Raised when an API request fails.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
    ):
        super().__init__(message, status_code)

    @property
    def message(self) -> str:
        return self.args[0]

    @property
    def status_code(self) -> int:
        return self.args[1]


class RioApi:
    """
    A wrapper around Rio's web API.
    """

    def __init__(
        self,
        access_token: str | None = None,
    ):
        self._access_token = access_token
        self._http_client = httpx.AsyncClient()

    @property
    def is_logged_in(self) -> bool:
        return self._access_token is not None

    async def __aenter__(self) -> "RioApi":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """
        Log out, if logged in and close the HTTP client.
        """
        if self.is_logged_in:
            try:
                await self.logout()
            except ApiException:
                pass

        await self._http_client.aclose()

    async def request(
        self,
        endpoint: str,
        *,
        method: Literal["get", "post", "delete"] = "get",
        json: dict[str, Any] | None = None,
        file: BinaryIO | None = None,
    ) -> Any:
        """
        Make a request to the Rio API.
        """
        # Build the request
        headers = {}
        if self._access_token is not None:
            headers["Authorization"] = f"Bearer {self._access_token}"

        if file is not None:
            files = {"file": file}
        else:
            files = None

        # Make the request
        #
        # TODO: Which exceptions can this throw?
        response = await self._http_client.request(
            method,
            f"{BASE_URL}/{endpoint}",
            headers=headers,
            json=json,
            files=files,
        )

        # Handle errors
        if response.status_code < 200 or response.status_code >= 300:
            raise ApiException(
                message=response.json()["message"],
                status_code=response.status_code,
            )

        # Return the response
        return response.json()

    async def login_with_name_and_password(
        self,
        username_or_email: str,
        password: str,
        *,
        requested_duration: timedelta = timedelta(days=1),
    ) -> None:
        """
        Log in to the Rio API using a username or email and password.

        If the client was already logged in before the old token is forgotten
        without being expired.
        """
        response = await self.request(
            "/auth/createTokenFromNameAndPassword",
            method="post",
            json={
                "usernameOrEmail": username_or_email,
                "password": password,
                "validForSeconds": requested_duration.total_seconds(),
            },
        )

        self._access_token = response["accessToken"]

    async def logout(self) -> None:
        """
        Log out of the Rio API, if logged in. Does nothing if not logged in.
        """
        if self._access_token is None:
            return

        await self.request("/auth/expireToken", method="post")

    async def get_user(self) -> dict[str, Any]:
        """
        Return the user's information, if logged in.
        """
        assert self.is_logged_in, "Must be logged in to get user info"
        return await self.request("/user/me")

    async def create_app(
        self,
        *,
        name: str,
        packed_app: BinaryIO,
        realm: Literal["pro", "free", "test"],
        start: bool,
    ) -> None:
        assert self.is_logged_in, "Must be logged in to create/update an app"

        await self.request(
            "/app/create",
            method="post",
            json={
                "name": name,
                "start": start,
            },
            file=packed_app,
        )
