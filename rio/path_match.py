import typing as t
from pathlib import Path

import gitignore_parser

__all__ = [
    "PathMatch",
]


class PathMatch:
    """
    Takes a list of paths to include / exclude and provides a method to check
    whether a given path should be included or excluded.

    This class uses the same syntax as `.gitignore` files, with the exceptions
    that a match is considered positive, while `.gitignore` files consider a
    match negative.
    """

    def __init__(
        self,
        base_dir: Path,
        *,
        rules: t.Iterable[str] = tuple(),
    ) -> None:
        self._base_dir = base_dir.resolve()
        self._rules: list[gitignore_parser.IgnoreRule] = []

        for rule in rules:
            self.add_rule(rule)

    def add_rule(self, line: str) -> None:
        """
        Add a rule to the include list.
        """
        # Parse the rule
        line = line.rstrip("\n")
        rule = gitignore_parser.rule_from_pattern(
            line,
            base_path=self._base_dir,
            source=(None, len(self._rules)),
        )

        # Empty line / comment
        if not rule:
            return

        self._rules.append(rule)

    def match(self, path: Path) -> bool:
        """
        Given a path, return whether the given path matches any of the rules.
        """
        for rule in reversed(self._rules):
            if rule.match(path):
                return not rule.negation

        return False
