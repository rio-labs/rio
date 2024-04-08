from pathlib import Path
from typing import *  # type: ignore

import gitignore_parser

__all__ = [
    "RioIgnore",
]


class RioIgnore:
    """
    Parses `.rioignore` files and allows querying whether a given path should be
    ignored.

    The actual rule matching is left to `gitignore_parser`, this class is just a
    wrapper making it easier to use and extending it slightly.
    """

    def __init__(self, base_dir: Path):
        self._base_dir = base_dir.resolve()
        self._rules: list[gitignore_parser.IgnoreRule] = []

    def add_pattern(self, line: str) -> None:
        """
        Add a pattern to the ignore list.
        """
        # Parse the pattern
        line = line.rstrip("\n")
        pattern = gitignore_parser.rule_from_pattern(
            line,
            base_path=self._base_dir,
            source=(None, len(self._rules)),
        )

        # Empty line / comment
        if not pattern:
            return

        self._rules.append(pattern)

    def add_patterns_from_file(self, file_path: TextIO) -> None:
        """
        Convenience method for adding all patterns from a file.
        """
        for line in file_path.readlines():
            self.add_pattern(line)

    def is_path_ignored(self, path: Path) -> bool:
        """
        Given a path, return whether the given path should be ignored, i.e.
        there is a rule matching it.
        """
        for rule in reversed(self._rules):
            if rule.match(path):
                return not rule.negation

        return False

    def is_explicitly_included(self, path: Path) -> bool:
        """
        Given a path, return whether there is an explicit exception for the
        file. A file is considered explicitly included if there is a rule
        of the form `!path`.
        """
        # Prepare the exact pattern which would match this path. This will also
        # find any paths which aren't in the basedirectory at all.
        try:
            pattern_should = f"!{path.relative_to(self._base_dir)}"
        except ValueError:
            return False

        # Compare all rules:
        for rule in self._rules:
            if rule.pattern.strip() == pattern_should:
                return True

        # No match
        return False
