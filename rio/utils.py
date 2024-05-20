from __future__ import annotations

import hashlib
import os
import re
import secrets
import socket
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import *  # type: ignore

import imy.assets
from PIL.Image import Image
from typing_extensions import Annotated
from yarl import URL

import rio

__all__ = [
    "EventHandler",
    "FileInfo",
    "ImageLike",
    "escape_markdown",
    "escape_markdown_code",
]


_SECURE_HASH_SEED: bytes = secrets.token_bytes(32)

# Expose common paths on the filesystem
PACKAGE_ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT_DIR = PACKAGE_ROOT_DIR.parent

GENERATED_DIR = PACKAGE_ROOT_DIR / "generated"

RIO_ASSETS_DIR = PACKAGE_ROOT_DIR / "assets"
HOSTED_ASSETS_DIR = RIO_ASSETS_DIR / "hosted"

RIO_LOGO_ASSET_PATH = HOSTED_ASSETS_DIR / "rio-logos/rio-logo-square.png"

SNIPPETS_DIR = PACKAGE_ROOT_DIR / "snippets" / "snippet-files"

if os.name == "nt":
    USER_CACHE_DIR = Path.home() / "AppData" / "Local" / "Cache"
    USER_CONFIG_DIR = Path.home() / "AppData" / "Roaming"
else:
    USER_CACHE_DIR = Path.home() / ".cache"
    USER_CONFIG_DIR = Path.home() / ".config"


# Constants & types
_READONLY = object()
T = TypeVar("T")
Readonly = Annotated[T, _READONLY]

ImageLike = Path | Image | URL | bytes


ASSET_MANGER: imy.assets.AssetManager = imy.assets.AssetManager(
    xz_dir=RIO_ASSETS_DIR,
    cache_dir=USER_CACHE_DIR / "rio",
    version=rio.__version__,
)


# Precompiled regexes
MARKDOWN_ESCAPE = re.compile(r"([\\`\*_\{\}\[\]\(\)#\+\-.!])")
MARKDOWN_CODE_ESCAPE = re.compile(r"([\\`])")


def secure_string_hash(*values: str, hash_length: int = 32) -> str:
    """
    Returns a reproducible, secure hash for the given values.

    The order of values matters. In addition to the given values a global seed
    is added. This seed is generated once when the module is loaded, meaning the
    result is not suitable to be persisted across sessions.
    """

    hasher = hashlib.blake2b(
        _SECURE_HASH_SEED,
        digest_size=hash_length,
    )

    for value in values:
        hasher.update(value.encode("utf-8"))

    return hasher.hexdigest()


@dataclass(frozen=True)
class FileInfo:
    """
    Contains information about a file.

    When asking the user to select a file, this class is used to represent the
    file. It contains metadata about the file, and can also be used to access
    the file's contents.

    Be careful when running your app as a webserver, since files will need to be
    uploaded by the user, which is a potentially very slow operation.


    ## Attributes

    `name`: The name of the file, including the extension.

    `size_in_bytes`: The size of the file, in bytes.

    `media_type`: The MIME type of the file, for example `text/plain` or
        `image/png`.
    """

    name: str
    size_in_bytes: int
    media_type: str
    _contents: bytes

    async def read_bytes(self) -> bytes:
        """
        Asynchronously reads the entire file as `bytes`.

        Reads and returns the entire file as a `bytes` object. If you know that
        the file is text, consider using `read_text` instead.
        """
        return self._contents

    async def read_text(self, *, encoding: str = "utf-8") -> str:
        """
        Asynchronously reads the entire file as text.

        Reads and returns the entire file as a `str` object. The file is decoded
        using the given `encoding`. If you don't know that the file is valid
        text, use `read_bytes` instead.

        ## Parameters

        encoding: The encoding to use when decoding the file.

        ## Raises

        UnicodeDecodeError: The file could not be decoded using the given
            `encoding`.
        """
        return self._contents.decode(encoding)

    @overload
    async def open(self, type: Literal["r"]) -> StringIO: ...

    @overload
    async def open(self, type: Literal["rb"]) -> BytesIO: ...

    async def open(self, type: Literal["r", "rb"] = "r") -> StringIO | BytesIO:
        """
        Asynchronously opens the file, as though it were a regular file on this
        device.

        Opens and returns the file as a file-like object. If 'r' is specified,
        the file is opened as text. If 'rb' is specified, the file is opened as
        bytes.

        Returns a file-like object containing the file's contents.

        ## Parameters

        type: The mode to open the file in. 'r' for text, 'rb' for bytes.
        """
        # Bytes
        if type == "rb":
            return BytesIO(await self.read_bytes())

        # UTF
        if type == "r":
            return StringIO(await self.read_text())

        # Invalid
        raise ValueError("Invalid type. Expected 'r' or 'rb'.")


T = TypeVar("T")
P = ParamSpec("P")

EventHandler = Callable[P, Any | Awaitable[Any]] | None


def make_url_relative(base: URL, other: URL) -> URL:
    """
    Returns `other` as a relative URL to `base`. Raises a `ValueError` if
    `other` is not a child of `base`.

    This will never generate URLs containing `..`. If those would be needed a
    `ValueError` is raised.
    """
    # Verify the URLs have the same scheme and host
    if base.scheme != other.scheme:
        raise ValueError(
            f'URLs have different schemes: "{base.scheme}" and "{other.scheme}"'
        )

    if base.host != other.host:
        raise ValueError(
            f'URLs have different hosts: "{base.host}" and "{other.host}"'
        )

    # Get the path segments of the URLs
    base_parts = base.parts
    other_parts = other.parts

    # Strip empty segments
    if base_parts and base_parts[-1] == "":
        base_parts = base_parts[:-1]

    if other_parts and other_parts[-1] == "":
        other_parts = other_parts[:-1]

    # See if the base is a parent of the other URL
    if base_parts != other_parts[: len(base_parts)]:
        raise ValueError(f'"{other}" is not a child of "{base}"')

    # Remove the common parts from the URL
    other_parts = other_parts[len(base_parts) :]
    return URL.build(
        path="/".join(other_parts),
        query=other.query,
        fragment=other.fragment,
    )


def escape_markdown(text: str) -> str:
    """
    Escape text such that it appears as-is when rendered as markdown.

    Given any text, this function returns a string which, when rendered as
    markdown, will look identical to the original text.


    ## Parameters

    `text`: The text to escape.
    """
    # TODO: Find a proper function for this. The current one is a total hack.
    return re.sub(MARKDOWN_ESCAPE, r"\\\1", text)


def escape_markdown_code(text: str) -> str:
    """
    Escape text such that it appears as-is inside a markdown code block.

    Given any text, this function returns a string which, when rendered inside a
    markdown code block, will look identical to the original text.


    ## Parameters

    `text`: The text to escape.
    """
    # TODO: Find a proper function for this. The current one is a total hack.
    return MARKDOWN_CODE_ESCAPE.sub(r"\\\1", text)


def choose_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind((host, port))
            return True
        except OSError as err:
            return False


def ensure_valid_port(host: str, port: int | None) -> int:
    if port is None:
        return choose_free_port(host)

    return port


def first_non_null(*values: T | None) -> T:
    """
    Returns the first non-`None` value, or raises a `ValueError` if all values
    are `None`.
    """

    for value in values:
        if value is not None:
            return value

    raise ValueError("At least one value must be non-`None`")


def _repr_build_function(build_function: Callable[[], rio.Component]) -> str:
    """
    Return a recognizable name for the provided function such as
    `Component.build`.
    """

    try:
        self = build_function.__self__  # type: ignore
    except AttributeError:
        return build_function.__qualname__

    return f"{type(self).__name__}.{build_function.__name__}"


def safe_build(build_function: Callable[[], rio.Component]) -> rio.Component:
    """
    Calls a build function and returns its result. This differs from just
    calling the function directly, because it catches any exceptions and returns
    a placeholder component instead. It will also ensure the returned value is
    in fact a component.
    """

    # Build the component
    try:
        build_result = build_function()

    # The function has crashed. Return a placeholder instead
    except Exception as err:
        build_function_repr = _repr_build_function(build_function)

        rio._logger.exception(
            f"An exception occurred in `{build_function_repr}`"
        )

        # Screw circular imports
        from rio.components.build_failed import BuildFailed

        build_failed_component = BuildFailed(
            f"`{build_function_repr}` has crashed", repr(err)
        )
    else:
        # Make sure the result meets expectations
        if isinstance(build_result, rio.Component):  # type: ignore (unnecessary isinstance)
            # All is well
            return build_result

        build_function_repr = _repr_build_function(build_function)

        rio._logger.error(
            f"The output of `build` methods must be instances of"
            f" `rio.Component`, but `{build_function_repr}` returned `{build_result!r}`"
        )

        # Screw circular imports
        from rio.components.build_failed import BuildFailed

        build_failed_component = BuildFailed(
            f"`{build_function_repr}` has returned an invalid result",
            f"Build functions must return instances of `rio.Component`, but the result was {build_result!r}",
        )

    # Save the error in the session, for testing purposes
    build_failed_component.session._crashed_build_functions[build_function] = (
        build_failed_component.error_details
    )

    return build_failed_component
