from pathlib import Path
from typing import *  # type: ignore

import keyring
import platformdirs
import tomlkit
from revel import fatal

from . import rio_api


class CliInstance:
    """
    Singleton class which abstracts away the environment for the Rio CLI. It
    handles access to commonly used functionality such as the configuration file
    and the API client.
    """

    _instance = None
    _config: tomlkit.TOMLDocument
    _api_client: rio_api.RioApi | None

    def __new__(cls):
        # Already initialized?
        if cls._instance is not None:
            return cls._instance

        # Nope, create a new instance
        self = cls._instance = super(CliInstance, cls).__new__(cls)

        # Read the config
        try:
            config_dir = Path(platformdirs.user_config_dir("rio"))
            self._config = tomlkit.loads(
                (config_dir / "config.toml").read_text()
            )
        except FileNotFoundError:
            self._config = tomlkit.document()
        except OSError as err:
            fatal(f"Couldn't read Rio's configuration: {err}")

        # Api client
        self._api_client = None

        return self

    async def __aenter__(self) -> "CliInstance":
        return self

    async def __aexit__(self, *args) -> None:
        if self._api_client is not None:
            await self._api_client.close()

    @property
    def auth_token(self) -> str | None:
        """
        Tries to get the auth token from the keyring. Returns `None` if no token
        was stored in the keyring yet.
        """
        return keyring.get_password("rio", "rioApiAuthToken")

    @auth_token.setter
    def auth_token(self, value: str) -> None:
        """
        Stores the given auth token in the keyring.
        """
        keyring.set_password("rio", "rioApiAuthToken", value)

    async def get_api_client(self, *, logged_in: bool = True) -> rio_api.RioApi:
        """
        Return an API client for the Rio API. If `logged_in` is True, the
        client will be authenticated, prompting the user to login if necessary.
        """
        # If there is no client yet, create one
        if self._api_client is None:
            self._api_client = rio_api.RioApi()

        # Authenticate, if necessary
        if logged_in and not self._api_client.is_logged_in:
            raise NotImplementedError("TODO: Login")

        return self._api_client
