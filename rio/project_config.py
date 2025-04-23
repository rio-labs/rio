from __future__ import annotations

import typing as t
from pathlib import Path

import path_imports
import revel
import tomlkit
import tomlkit.exceptions
import tomlkit.items
import uniserde

import rio

from . import path_match

__all__ = ["RioProjectConfig"]

T = t.TypeVar("T")


DEFAULT_FATAL = object()
DEFAULT_KEYERROR = object()


DEFAULT_PROJECT_FILES_GLOB_PATTERNS: t.Iterable[str] = (
    "*.py",
    "/assets/",
    "/rio.toml",
)


class RioProjectConfig:
    def __init__(
        self,
        *,
        file_path: Path,
        toml_dict: uniserde.JsonDoc,
        dirty_keys: set[tuple[str, str]],
    ) -> None:
        # Path to the `rio.toml` file. May or may not exist
        self.rio_toml_path = file_path

        # Which sections & keys have been modified and thus must be written back
        # to the `rio.toml` file. Entries in here don't necessarily have to
        # exist in `self._toml_dict`, because the change made to them was to
        # delete them.
        #
        # This must be initialized before populating, because it is accessed by
        # that function.
        self._dirty_keys: set[tuple[str, str]] = dirty_keys

        # All of the data from the `rio.toml` file, reorganized into the format
        #
        # {
        #   (section, key): value
        # }
        self._toml_dict: dict[tuple[str, str], t.Any] = {}
        self._replace_from_dictionary(toml_dict)

    def _replace_from_dictionary(self, raw: uniserde.JsonDoc) -> None:
        """
        Discards any values in the internal `_toml_dict` and `_dirty_keys` and
        re-populates them with the contents of the passed dictionary. Any
        root-level dictionaries are treated as sections. Any other values are
        silently ignored.
        """
        # Drop any existing values
        self._toml_dict.clear()
        self._dirty_keys.clear()

        # Add the new values
        for section_name, section in raw.items():
            if not isinstance(section, dict):
                continue

            for key_name, value in section.items():
                self._toml_dict[section_name, key_name] = value

        # Replace deprecated names with the new ones
        try:
            app_type = self._toml_dict.pop(("app", "app_type"))
        except KeyError:
            pass
        else:
            self._toml_dict[("app", "app-type")] = app_type
            self._dirty_keys.add(("app", "app_type"))
            self._dirty_keys.add(("app", "app-type"))

        try:
            main_module = self._toml_dict.pop(("app", "main_module"))
        except KeyError:
            pass
        else:
            self._toml_dict[("app", "main-module")] = main_module
            self._dirty_keys.add(("app", "main_module"))
            self._dirty_keys.add(("app", "main-module"))

    def get_key(
        self,
        section_name: str,
        key_name: str,
        key_type: t.Type[T],
        default_value: t.Any,
    ) -> T:
        """
        Fetches the value of a key from the `rio.toml` file. If the key is
        missing, and a default value was provided it is returned instead.

        If the default value is `DEFAULT_FATAL`, an error is displayed and the
        program exits.

        If the default value is `DEFAULT_KEYERROR`, a `KeyError` is raised.
        """
        # Try to get the key
        try:
            value = self._toml_dict[(section_name, key_name)]

        # There is no value, use the default
        except KeyError:
            if default_value is DEFAULT_FATAL:
                revel.fatal(
                    f"`rio.toml` is missing the `{key_name}` key. Please add it"
                    f" to the [[{section_name}] section.",
                    status_code=1,
                )

            if default_value is DEFAULT_KEYERROR:
                raise KeyError(key_name)

            value = default_value

        # Make sure the value is the correct type
        if isinstance(value, key_type):
            return value

        if key_type is float and isinstance(value, int):
            return value  # type: ignore

        raise TypeError(
            f"`rio.toml` contains an invalid value for `{key_name}`: expected"
            f" {key_type}, got {type(value).__name__}",
        )

    def set_key(self, section_name: str, key_name: str, value: t.Any) -> None:
        """
        Sets the value of a key in the `rio.toml` file. The value is not written
        to disk until `write()` is called.
        """
        # Set the value
        self._toml_dict[(section_name, key_name)] = value

        # Consider it dirty
        self._dirty_keys.add((section_name, key_name))

    @property
    def project_directory(self) -> Path:
        """
        The projects root directory. This is the same directory containing
        `rio.toml`.
        """
        return self.rio_toml_path.parent

    @property
    def app_type(self) -> t.Literal["app", "website"]:
        """
        Whether this project is a website or local app.
        """
        result = self.get_key("app", "app-type", str, "website")

        if result not in ("app", "website"):
            revel.fatal(
                f"`rio.toml` contains an invalid value for `app.app-type`: It should be either `app` or `website`, not `{result}`"
            )

        return result

    @app_type.setter
    def app_type(self, value: t.Literal["app", "website"]) -> None:
        self.set_key("app", "app-type", value)

    @property
    def app_main_module_name(self) -> str:
        return self.get_key("app", "main-module", str, DEFAULT_FATAL)

    def find_app_main_module_path(self) -> Path:
        """
        The path to the project's main Python module. This is the module which
        exposes a `rio.App` instance which is used to start the app.
        """
        # If a `src` folder exists, look there as well
        for folder in (self.project_directory / "src", self.project_directory):
            module_path = path_imports.find_module_location(
                self.app_main_module_name, directory=folder
            )

            if module_path is not None:
                return module_path

        raise FileNotFoundError(
            f"There is no {self.app_main_module_name!r} module in {self.project_directory!r}"
        )

    @property
    def project_files_glob_patterns(self) -> t.Iterable[str]:
        """
        Each project includes a list of files which are considered to be part of
        the project. These files are specified using glob patterns. This
        property returns those patterns.
        """
        return self.get_key(
            "app",
            "project-files",
            list,
            list(DEFAULT_PROJECT_FILES_GLOB_PATTERNS),
        )

    @project_files_glob_patterns.setter
    def project_files_glob_patterns(self, value: t.Iterable[str]) -> None:
        self.set_key("app", "project-files", list(value))

    def file_is_path_of_project(self, file_path: Path) -> bool:
        """
        Returns whether the passed file path is considered to be part of the
        project. This is determined by checking if the file path matches any of
        the project's glob patterns.

        This does not access the file system, or perform any checks whether the
        fil exists. It simply compares the path to the project's glob patterns.
        """
        # This is a more complex task than it might seem at first. Use a helper
        # class to do the heavy lifting
        matcher = path_match.PathMatch(
            base_dir=self.project_directory,
            rules=self.project_files_glob_patterns,
        )

        # See if the path matches
        return matcher.match(file_path)

    @property
    def deployment_app_id(self) -> str | None:
        """
        A unique ID used by Rio's API to refer to apps. If no ID has been
        set yet, this returns `None`. Deploy the app to the API to get an ID.

        Note that the result of this is strictly a string. While it may look
        like an `ObjectId` from MongoDB, the API does not guarantee this, and so
        the value is best left unparsed.
        """
        return self.get_key(
            "deployment",
            "app-id",
            str,
            None,
        )

    @deployment_app_id.setter
    def deployment_app_id(self, value: str) -> None:
        """
        Sets the app ID. This is used by the API to refer to the app.
        """
        self.set_key(
            "deployment",
            "app-id",
            value,
        )

    # @functools.cached_property
    # def deploy_name(self) -> str:
    #     # Is a name already stored in the `rio.toml`?
    #     try:
    #         return self.get_key("deploy", "name", str, DEFAULT_KEYERROR)
    #     except KeyError:
    #         pass

    #     # Ask the user for a name, and make sure it's suitable for URLs
    #     print(
    #         "What should your app be called? This name will be used as part of the URL."
    #     )
    #     print(
    #         'For example, if you name your app "my-app", it will be deployed at `https://rio.dev/.../my-app`.'
    #     )

    #     while True:
    #         name = input("App name: ")

    #         allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789-"
    #         normalized = re.sub("[^" + allowed_chars + "]", "-", name.lower())

    #         if name == normalized:
    #             break

    #         normalized = re.sub("-+", "-", normalized)
    #         print(
    #             f"`{name}` cannot be used for app names. Is `{normalized}` okay?"
    #         )

    #         if revel.select_yes_no("", default_value=True):
    #             name = normalized
    #             break

    #     # Store the name
    #     self.set_key("deploy", "name", name)
    #     return name

    @staticmethod
    def create_interactively(
        project_directory: Path | None = None,
    ) -> RioProjectConfig:
        """
        Interactively generates the contents for a new `rio.toml` file. The file
        is both written to disk and returned as dictionary. Writing to disk is
        important, because it allows adding comments.
        """
        if project_directory is None:
            project_directory = find_or_guess_project_directory()

        assert project_directory.exists(), project_directory
        assert project_directory.is_dir(), project_directory

        # Find the main module
        main_module_name: str | None = None

        for subpath in project_directory.iterdir():
            if subpath.is_file():
                continue

            if subpath.is_dir() and (subpath / "__init__.py").exists():
                main_module_name = subpath.name
                break

        prompt = "What is the name of the main module?"

        if main_module_name is None:
            main_module_name = revel.input(prompt=prompt)
        else:
            main_module_name = revel.input(
                prompt="What is the name of the main module?",
                default=main_module_name,
            )

        return RioProjectConfig.create(
            project_directory / "rio.toml",
            main_module=main_module_name,
            project_type="website",
        )

    @staticmethod
    def create(
        path: Path,
        *,
        main_module: str,
        project_type: t.Literal["app", "website"],
    ) -> RioProjectConfig:
        """
        Write a new `rio.toml` file at the given file path. This file will
        contain the default values for a new project as well as useful comments
        for the user.

        Note: Unlike the constructor of this class, this method has the side
        effect that the file is immediately written to disk.
        """

        # Create the toml document
        rio_toml = tomlkit.document()
        rio_toml.add(
            tomlkit.comment(
                "This is the configuration file for Rio, an easy to use app & web framework for"
            )
        )
        rio_toml.add(tomlkit.comment("Python."))

        # Add the [app] section
        app_section = tomlkit.table()
        rio_toml["app"] = app_section

        app_section.add(tomlkit.comment('This is either "website" or "app"'))
        app_section.add("app-type", project_type)

        app_section.add(tomlkit.nl())
        app_section.add(tomlkit.comment("The name of your Python module"))
        app_section.add("main-module", main_module)

        app_section.add(tomlkit.nl())
        app_section.add(
            tomlkit.comment(
                "All files which are part of your project. Changes to these will trigger a"
            )
        )
        app_section.add(
            tomlkit.comment("reload and they will be packed up when deploying.")
        )
        app_section.add(
            "project-files", list(DEFAULT_PROJECT_FILES_GLOB_PATTERNS)
        )

        # Write the resulting file
        with path.open("w", encoding="utf-8") as file:
            file.write(tomlkit.dumps(rio_toml))

        return RioProjectConfig(
            file_path=path,
            toml_dict=rio_toml.unwrap(),
            dirty_keys=set(),
        )

    @staticmethod
    def try_locate_and_load() -> RioProjectConfig:
        """
        Best-effort attempt to locate the project directory and load the
        `rio.toml` file. Throws `FileNotFoundError` if the file can't be found.

        ## Raises

        `OSError`: (and subclasses) If the file can't be read due to
            permissions, doesn't exist or similar.
        """
        # Search upward until a `rio.toml` is found
        for project_dir in iter_directories_upward():
            # Is this the project directory?
            rio_toml_path = project_dir / "rio.toml"

            if rio_toml_path.exists():
                break
        else:
            raise FileNotFoundError("rio.toml not found")

        with rio_toml_path.open() as f:
            rio_toml_dict = tomlkit.load(f).unwrap()

        # Instantiate the project config
        return RioProjectConfig(
            file_path=rio_toml_path,
            toml_dict=rio_toml_dict,
            dirty_keys=set(),
        )

    @staticmethod
    def load_or_create_interactively() -> RioProjectConfig:
        """
        Best-effort attempt to locate the project directory and load the
        `rio.toml` file. This will offer to create a new project if one isn't
        found.

        **This function doesn't raise. It prints problems to the terminal and
        exits the entire process.**
        """
        # Try to load the project config
        try:
            return RioProjectConfig.try_locate_and_load()

        # No such file. Offer to create one
        except FileNotFoundError:
            revel.warning(
                f"You don't appear to be inside of a [bold primary]Rio[/] project. Would you like to create one?"
            )

            if not revel.select_yes_no("", default_value=True):
                revel.fatal(
                    f"Couldn't find `rio.toml`.",
                    status_code=1,
                )

            return RioProjectConfig.create_interactively()

        # Anything OS related
        except OSError as e:
            revel.fatal(
                f"Cannot read `rio.toml`: {e}",
                status_code=1,
            )

        # Invalid syntax
        except tomlkit.exceptions.TOMLKitError as e:
            revel.fatal(
                f"There is a problem with `rio.toml`: {e}",
                status_code=1,
            )

    def discard_changes_and_reload(self) -> None:
        """
        Reload the `rio.toml` file, discarding any latent changes.

        ## Raises

        `OSError`: (and subclasses) If the file can't be read due to permissions
            or similar.

        `InvalidProjectConfigError`: If the configuration file exists, but
            cannot be read (e.g. due to being invalid TOML).
        """
        # Read all values from the `rio.toml` file
        try:
            with self.rio_toml_path.open() as f:
                raw_toml_dict = tomlkit.load(f).unwrap()

        # OSErrors are propagated. TOML-related errors shouldn't leak through
        # though.
        except tomlkit.exceptions.TOMLKitError as e:
            raise rio.InvalidProjectConfigError(
                f"Couldn't read `{self.rio_toml_path}`: {e}"
            )

        # Populate the internal values. This will also clear them.
        self._replace_from_dictionary(raw_toml_dict)

    def __enter__(self) -> RioProjectConfig:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        # Make sure to write any changes back to the `rio.toml` file
        self.write()

    def write(self) -> None:
        """
        Write any changes back to the `rio.toml` file.
        """
        rio._logger.debug(f"Writing `{self.rio_toml_path}`")

        # Make sure the parent directory exists
        self.rio_toml_path.parent.mkdir(parents=True, exist_ok=True)

        # Fetch an up-to-date copy of the file contents, with all formatting
        # intact
        try:
            new_toml_dict = tomlkit.loads(self.rio_toml_path.read_text())

        # If it can't be read, preserve all known values
        except (OSError, tomlkit.exceptions.TOMLKitError):
            new_toml_dict = tomlkit.TOMLDocument()
            self._dirty_keys = set(self._toml_dict.keys())

        # Avoid writing the file if nothing changed
        if not self._dirty_keys:
            return

        # Update the freshly read toml with all latent changes
        for section_name, key_name in self._dirty_keys:
            # Get the section from the on-disk toml
            try:
                section = new_toml_dict[section_name]
            except KeyError:
                section = new_toml_dict[section_name] = tomlkit.table()

            # Get the key from the in-memory section. If it can't be found, the
            # key was deleted
            try:
                value = self._toml_dict[(section_name, key_name)]
            except KeyError:
                del section[key_name]  # type: ignore
            else:
                section[key_name] = value  # type: ignore

        # Write the file
        try:
            with self.rio_toml_path.open("w") as f:
                tomlkit.dump(new_toml_dict, f)

        except OSError as e:
            revel.fatal(
                f"Couldn't write `{self.rio_toml_path}`: {e}",
                status_code=1,
            )

        # The project's keys are now clean
        self._dirty_keys.clear()


def find_or_guess_project_directory() -> Path:
    """
    Looks for a directory that looks like a python project, starting at the CWD.
    If none is found, the CWD is returned.
    """
    for project_dir in iter_directories_upward():
        if (project_dir / "pyproject.toml").exists():
            return project_dir

    return Path.cwd()


def iter_directories_upward(path: Path | None = None) -> t.Iterable[Path]:
    if path is None:
        path = Path.cwd().absolute()

    yield path
    yield from path.parents
