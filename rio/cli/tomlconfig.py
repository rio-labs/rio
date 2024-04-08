from pathlib import Path
from typing import Any

import tomlkit
import tomlkit.exceptions


class TomlConfig:
    """
    Easy way to load and save configuration files in TOML format.

    The configuration file is loaded once, and then cached. Any modified values
    are remembered and written back in one go later on. Writing changes to the
    file is done atomically and preserves comments and formatting in the file.
    """

    def __init__(
        self,
        config_path: Path,
        *,
        default: dict[str, Any] = {},
    ):
        # Where to load the config from and save it back to
        self.config_path = config_path

        # Default values to use if the config file or any entries don't exist
        self.default = default

        # The configuration file's contents
        self._config: dict[str, Any] = {}
        self._load()

        # Keeps track of any keys which were changed and need to be written back
        self._dirty_keys: dict[tuple[str, ...], Any] = {}

    def _load(self) -> None:
        """
        Load the contents from `self.config_path` and store them in
        `self._config`.
        """
        assert not self._config

        # Try to load the toml file
        try:
            self._config = tomlkit.load(
                self.config_path.open()
            ).unwrap()  # TODO: Does this have to be done recursively?

        # No such file. Use the default values
        except FileNotFoundError:
            self._config = self.default
            return

    def save(self) -> None:
        """
        Write any changes back to the `self.config_path` file.
        """
        # Are there even any changes to write?
        if not self._dirty_keys:
            return

        # Make sure the parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Fetch an up-to-date copy of the file contents, with all formatting
        # intact
        try:
            with self.config_path.open() as f:
                new_toml_dict = tomlkit.load(f)

        # If it can't be read, preserve all known values
        except (OSError, tomlkit.exceptions.TOMLKitError) as e:
            new_toml_dict = tomlkit.TOMLDocument()

            for key, value in self._config.items():
                new_toml_dict[key] = value

        # Otherwise add just the dirty keys
        else:
            for key, value in self._dirty_keys.items():
                for subkey in key[:-1]:
                    new_toml_dict.setdefault(subkey, {})

                new_toml_dict[key[-1]] = value

        # Dump the new TOML
        with self.config_path.open("w") as f:
            tomlkit.dump(new_toml_dict, f)

        # All values have been saved and are now clean
        self._dirty_keys.clear()

    def __enter__(self) -> "TomlConfig":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        # Make sure to write any changes back to the `rio.toml` file
        self.save()

    def __getitem__(self, *key: str) -> Any:
        current_dict = self._config

        for subkey in key:
            try:
                current_dict = current_dict[subkey]
            except KeyError:
                raise KeyError(key) from None

        return current_dict

    def __setitem___(self, *key: str, value: Any) -> None:
        """
        Sets the value of a key in configuration. The value is not written back
        to disk until `write()` is called.
        """
        # Add the value to the config
        current_dict = self._config

        for ii, subkey in enumerate(key[:-1]):
            current_dict = current_dict.setdefault(subkey, {})

            if not isinstance(current_dict, dict):
                key_until_now = key[: ii + 1]
                raise ValueError(f"`{key_until_now}` is not a dictionary")

        current_dict[key[-1]] = value

        # Remember that this key was changed
        self._dirty_keys[key] = value
