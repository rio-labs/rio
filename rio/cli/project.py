from __future__ import annotations

import functools
from pathlib import Path
from typing import *  # type: ignore

import revel
import tomlkit
import tomlkit.exceptions
import tomlkit.items
import uniserde
from revel import *  # type: ignore

import rio

from . import path_match

__all__ = [
    "RioProject",
]

T = TypeVar("T")


DEFAULT_FATAL = object()
DEFAULT_KEYERROR = object()


DEFAULT_PROJECT_FILES_GLOB_PATTERNS: Iterable[str] = (
    "*.py",
    "/assets/",
    "/rio.toml",
)


class RioProject:
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
        self._toml_dict: dict[tuple[str, str], Any] = {}
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

    @staticmethod
    def write_new_rio_toml(
        out: IO[str],
        main_module: str,
        project_type: Literal["website", "app"],
    ) -> dict[str, Any]:
        """
        Write a new `rio.toml` file to the passed file object. This file will
        contain the default values for a new project as well as useful comments
        for the user.
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

        app_section.add(tomlkit.comment("The name of your Python module"))
        app_section.add("main-module", main_module)

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
        out.write(tomlkit.dumps(rio_toml))

        # And also return it as dictionary
        return rio_toml.unwrap()

    def get_key(
        self,
        section_name: str,
        key_name: str,
        key_type: Type[T],
        default_value: Any,
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
                fatal(
                    f"`rio.toml` is missing the `{key_name}` key. Please add it to the [[{section_name}] section.",
                    status_code=1,
                )

            if default_value is DEFAULT_KEYERROR:
                raise KeyError(key_name)

            value = default_value

        # Make sure the value is the correct type
        if not isinstance(value, key_type) and not (
            key_type is float and isinstance(value, int)
        ):
            fatal(
                f"`rio.toml` contains an invalid value for `{key_name}`: expected {key_type}, got {type(value)}",
                status_code=1,
            )

        # Done
        return value  # type: ignore

    def set_key(self, section_name: str, key_name: str, value: Any) -> None:
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
    def app_type(self) -> Literal["app", "website"]:
        """
        Whether this project is a website or local app.
        """
        result = self.get_key("app", "app_type", str, "website")

        if result not in ("app", "website"):
            fatal(
                f"`rio.toml` contains an invalid value for `app.app_type`: It should be either `app` or `website`, not `{result}`"
            )

        return result

    @app_type.setter
    def app_type(self, value: Literal["app", "website"]) -> None:
        self.set_key("app", "app-type", value)

    @property
    def app_main_module(self) -> str:
        return self.get_key("app", "main-module", str, DEFAULT_FATAL)

    @functools.cached_property
    def app_main_module_path(self) -> Path:
        """
        The path to the project's root Python module. This is the module which
        exposes a `rio.App` instance which is used to start the app.
        """
        folder = self.project_directory

        # If a `src` directory exists, look there
        src_dir = folder / "src"
        if src_dir.exists():
            folder = src_dir

        # If a package (folder) exists, use that
        module_path = folder / self.app_main_module
        if module_path.exists():
            return module_path

        # Otherwise there must be a file
        return module_path.with_name(self.app_main_module + ".py")

    @property
    def project_files_glob_patterns(self) -> Iterable[str]:
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
    def project_files_glob_patterns(self, value: Iterable[str]) -> None:
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
    def _create_toml_contents_interactively(
        project_directory: Path,
    ) -> dict[str, Any]:
        """
        Interactively generates the contents for a new `rio.toml` file. The file
        is both written to disk and returned as dictionary. Writing to disk is
        important, because it allows adding comments.
        """
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

        # Write the result
        with (project_directory / "rio.toml").open("w", encoding="utf-8") as f:
            result = RioProject.write_new_rio_toml(
                f,
                main_module=main_module_name,
                project_type="website",
            )

        return result

    @staticmethod
    def try_locate_and_load() -> RioProject:
        """
        Best-effort attempt to locate the project directory and load the
        `rio.toml` file. This will offer to create a new project if one isn't
        found.
        """
        # Search upward until a `rio.toml` is found
        root_search_dir = Path.cwd()
        project_dir = root_search_dir

        while True:
            # Is this the project directory?
            rio_toml_path = project_dir / "rio.toml"

            if rio_toml_path.exists():
                break

            # Go up a directory, if possible
            parent_dir = project_dir.parent

            if parent_dir == project_dir:
                project_dir = root_search_dir
                break

            project_dir = parent_dir

        # Try to load the toml file
        rio_toml_path = project_dir / "rio.toml"

        try:
            with rio_toml_path.open() as f:
                rio_toml_dict = tomlkit.load(f).unwrap()

        # No such file. Offer to create one
        except FileNotFoundError:
            warning(
                f"You don't appear to be inside of a [bold primary]Rio[/] project. Would you like to create one?"
            )

            if not revel.select_yes_no("", default_value=True):
                fatal(
                    f"Couldn't find `rio.toml`.",
                    status_code=1,
                )

            rio_toml_dict = RioProject._create_toml_contents_interactively(
                project_dir
            )

        # Anything OS related
        except OSError as e:
            fatal(
                f"Cannot read `{rio_toml_path}`: {e}",
                status_code=1,
            )

        # Invalid syntax
        except tomlkit.exceptions.TOMLKitError as e:
            fatal(
                f"There is a problem with `rio.toml`: {e}",
                status_code=1,
            )

        # Instantiate the project
        return RioProject(
            file_path=rio_toml_path,
            toml_dict=rio_toml_dict,
            dirty_keys=set(),
        )

    def discard_changes_and_reload(self) -> None:
        """
        Reload the `rio.toml` file, discarding any latent changes.
        """
        # Read all values from the `rio.toml` file
        with self.rio_toml_path.open() as f:
            raw_toml_dict = tomlkit.load(f).unwrap()

        # Populate the internal values. This will also clear them.
        self._replace_from_dictionary(raw_toml_dict)

    def __enter__(self) -> "RioProject":
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
        except (OSError, tomlkit.exceptions.TOMLKitError) as e:
            new_toml_dict = tomlkit.TOMLDocument()
            self._dirty_keys = set(self._toml_dict.keys())

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
            fatal(
                f"Couldn't write `{self.rio_toml_path}`: {e}",
                status_code=1,
            )

        # The project's keys are now clean
        self._dirty_keys.clear()
