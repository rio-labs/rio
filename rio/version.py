import dataclasses
import typing as t

import typing_extensions as te


@dataclasses.dataclass(frozen=True)
class Version:
    major: int
    minor: int = 0
    patch: int = 0
    rc: int | None = None

    @classmethod
    def parse(cls, version_string: str) -> te.Self:
        """
        Quick & dirty version parser, useful for comparing versions.

        The results are the major, minor and patch version numbers. The final value
        is negative if the version is a pre-release version and zero otherwise.

        This function is best-effort and only supports version schemes as currently
        used by Rio. It will fail with a `ValueError` if the version string is
        invalid, or simply not supported. Guard against that!
        """
        head, _, tail = version_string.partition("rc")

        if tail:
            rc = int(tail)
        else:
            rc = None

        parts = head.split(".")
        parts += ("0", "0", "0")

        return cls(
            major=int(parts[0]),
            minor=int(parts[1]),
            patch=int(parts[2]),
            rc=rc,
        )

    def bump_major(self) -> te.Self:
        return type(self)(major=self.major + 1)

    def bump_minor(self) -> te.Self:
        return type(self)(major=self.major, minor=self.minor + 1)

    def bump_patch(self) -> te.Self:
        return type(self)(
            major=self.major,
            minor=self.minor,
            patch=self.patch + 1,
        )

    def bump_rc(self) -> te.Self:
        return type(self)(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            rc=0 if self.rc is None else self.rc + 1,
        )

    def drop_rc(self) -> te.Self:
        return type(self)(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            rc=None,
        )

    def __gt__(self, other: t.Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        if self.major != other.major:
            return self.major > other.major

        if self.minor != other.minor:
            return self.minor > other.minor

        if self.patch != other.patch:
            return self.patch > other.patch

        if self.rc is None:
            return other.rc is not None

        if other.rc is None:
            return False

        return self.rc > other.rc

    def __str__(self) -> str:
        version_string = f"{self.major}.{self.minor}"

        if self.patch > 0:
            version_string += f".{self.patch}"

        if self.rc is not None:
            version_string += f"rc{self.rc}"

        return version_string
