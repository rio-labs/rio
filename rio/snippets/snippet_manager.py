from __future__ import annotations

import dataclasses
import re
import typing as t
from pathlib import Path

__all__ = [
    "Snippet",
    "SnippetManager",
]


SECTION_PATTERN = re.compile(r" *#\s*<(\/?[\w-]+)>")


@dataclasses.dataclass
class Snippet:
    # The group the snippet is in
    group: str

    # The name the snippet can be accessed with
    name: str

    # The path to the snippet file
    file_path: Path

    # For text snippets, this is the raw file contents. `None` for binary
    # snippets.
    raw_code: str | None

    @property
    def is_text_snippet(self) -> bool:
        return self.raw_code is not None

    @property
    def is_binary_snippet(self) -> bool:
        return not self.is_text_snippet

    @staticmethod
    def from_path(group: str, name: str, file_path: Path) -> Snippet:
        # Read the contents if it's a text snippet
        if file_path.suffix in (".txt", ".md", ".py", ".json"):
            raw_code = file_path.read_text(encoding="utf-8")

            # The example projects contain a bunch of imports that can't be
            # resolved, so those are marked with special `# type: ignore`
            # comments that need to be removed
            if file_path.suffix == ".py":
                raw_code = raw_code.replace(
                    "  # type: ignore (hidden from user)", ""
                )
        else:
            raw_code = None

        return Snippet(
            group=group,
            name=name,
            file_path=file_path,
            raw_code=raw_code,
        )

    def get_section(self, section_name: str) -> str:
        assert self.is_text_snippet, self
        assert self.raw_code is not None, self  # For the type checker

        # Find the target section
        lines = self.raw_code.splitlines()
        section_found = False
        result = []

        for line in lines:
            match = SECTION_PATTERN.match(line)

            # No match
            if match is None:
                result.append(line)
                continue

            # Start of the target section?
            if match.group(1) == section_name:
                result = []
                section_found = True
                continue

            # End of the target section?
            if match.group(1) == f"/{section_name}":
                return "\n".join(result)

            # Some other section, drop it
            pass

        # The section was never found
        if not section_found:
            raise KeyError(f"There is no section named `{section_name}`")

        # The section was found, but never closed
        raise ValueError(f"The section `{section_name}` was never closed")

    def stripped_code(self) -> str:
        """
        Returns the given code with all section tags removed.
        """
        assert self.is_text_snippet, self
        assert self.raw_code is not None, self  # For the type checker

        lines = self.raw_code.splitlines()

        # Remove all section tags
        result = []
        for line in lines:
            if SECTION_PATTERN.match(line) is None:
                result.append(line)

        return "\n".join(result)


class SnippetManager:
    """
    A class the helps load snippets from a directory, caching the results.
    """

    def __init__(self, snippet_directory: Path) -> None:
        # The directory containing all snippet groups
        self._snippet_directory = snippet_directory

        # Once initialized, stores all snippets by group and name. Instead of
        # accessing this value directly, call `_get_snippet_cache()`. That
        # function ensures that the cache has been initialized and returns it.
        self._snippet_cache: dict[str, dict[str, Snippet]] | None = None

    def _get_all_snippet_paths(self) -> dict[str, dict[str, Path]]:
        """
        Returns a dictionary containing all available snippets. The snippets are
        organized by group and name.
        """
        # Find all snippet files
        result = {}

        def scan_dir_recursively(group_name: str, path: Path) -> None:
            assert path.is_dir(), path
            assert result is not None

            # Exclude some directories
            if path.name == "__pycache__":
                return

            for fpath in path.iterdir():
                # Directory
                if fpath.is_dir():
                    scan_dir_recursively(group_name, fpath)

                # Snippet file
                else:
                    name = fpath.name
                    group = result.setdefault(group_name, {})
                    group[name] = fpath

        # Scan all snippet directories. The first directory is used as a key, the
        # rest just for organization.
        for group_dir in self._snippet_directory.iterdir():
            assert group_dir.is_dir(), group_dir
            scan_dir_recursively(group_dir.name, group_dir)

        return result

    def _get_snippet_cache(self) -> dict[str, dict[str, Snippet]]:
        """
        Ensures that the snippet cache has been initialized. If it hasn't
        snippets are loaded from disk first, then returned.

        This will always return the same dictionary instance. Thus the result
        must not be modified.
        """
        # If the cache has already been initialized, return it
        if self._snippet_cache is not None:
            return self._snippet_cache

        # Load all snippets
        self._snippet_cache = {}

        for group_name, snippets in self._get_all_snippet_paths().items():
            group_dict = self._snippet_cache[group_name] = {}

            for name, file_path in snippets.items():
                group_dict[name] = Snippet.from_path(
                    group_name,
                    name,
                    file_path,
                )

        return self._snippet_cache

    def get_snippet(self, group: str, name: str) -> Snippet:
        """
        Gets the snippet with the given group and name.

        This function always returns the same snippet instance for a given
        group and name. Thus the result must not be modified.

        ## Raises

        `KeyError`: If there is no snippet with the given group and name.
        """
        all_groups = self._get_snippet_cache()

        group_dict = all_groups[group]
        return group_dict[name]

    def get_all_snippet_groups(self) -> set[str]:
        """
        Returns a set of all available snippet groups.
        """
        all_groups = self._get_snippet_cache()
        return set(all_groups.keys())

    def get_all_snippets_in_group(self, group: str) -> t.Iterable[Snippet]:
        """
        Returns all snippets in the given group.

        This function always returns the same snippet instances for a given
        group. Thus the result must not be modified.

        ## Raises

        `KeyError`: If there is no group with the given name.
        """
        all_groups = self._get_snippet_cache()
        group_dict = all_groups[group]
        return tuple(group_dict.values())
