from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import secrets
import socket
import typing as t
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path

import imy.assets
import typing_extensions as te
from PIL.Image import Image
from yarl import URL

import rio

__all__ = [
    "EventHandler",
    "FileInfo",
    "ImageLike",
    "escape_markdown",
    "escape_markdown_code",
    "i_know_what_im_doing",
]


# Sentinel type & value for when no value is provided and `None` would be
# unacceptable.
#
# To use this, use `NotGiven` as the type hint and `NOT_GIVEN` as the default
# value. Then, for checking the value, use `isinstance(value, NotGiven)`. While
# `value is NOT_GIVEN` would work, it is not recommended because it makes the
# type checker believe that the value could be another instance of `NotGiven`,
# even though there are no other instances.
#
# ## Example
#
# ```python
# def my_function(value: NotGiven = NOT_GIVEN) -> None:
#     if isinstance(value, NotGiven):
#         raise ValueError("You fool!")
#
#     # Do something with the value
# ```


class NotGiven:
    pass


NOT_GIVEN = NotGiven()


_SECURE_HASH_SEED: bytes = secrets.token_bytes(32)

# Expose common paths on the filesystem
PACKAGE_ROOT_DIR = Path(__file__).absolute().parent
PROJECT_ROOT_DIR = PACKAGE_ROOT_DIR.parent

RIO_ASSETS_DIR = PACKAGE_ROOT_DIR / "assets"
HOSTED_ASSETS_DIR = RIO_ASSETS_DIR / "hosted"

FRONTEND_FILES_DIR = PACKAGE_ROOT_DIR / "frontend files"
FRONTEND_ASSETS_DIR = FRONTEND_FILES_DIR / "assets"

RIO_LOGO_ASSET_PATH = HOSTED_ASSETS_DIR / "rio_logos/rio_logo_square.png"

SNIPPETS_DIR = PACKAGE_ROOT_DIR / "snippets" / "snippet-files"

if os.name == "nt":
    USER_CACHE_DIR = Path.home() / "AppData" / "Local" / "Cache"
    USER_CONFIG_DIR = Path.home() / "AppData" / "Roaming"
else:
    USER_CACHE_DIR = Path.home() / ".cache"
    USER_CONFIG_DIR = Path.home() / ".config"


# Constants & types
_READONLY = object()
T = t.TypeVar("T")
Readonly = te.Annotated[T, _READONLY]

ImageLike = Path | Image | URL | bytes


ASSET_MANAGER: imy.assets.AssetManager = imy.assets.AssetManager(
    xz_dir=RIO_ASSETS_DIR,
    cache_dir=USER_CACHE_DIR / "rio",
    version=rio.__version__,
)


# Precompiled regex patterns
MARKDOWN_ESCAPE = re.compile(r"([\\`\*_\{\}\[\]\(\)#\+\-.!])")
MARKDOWN_CODE_ESCAPE = re.compile(r"([\\`])")


I_KNOW_WHAT_IM_DOING = set[object]()


def i_know_what_im_doing(thing: t.Callable):
    I_KNOW_WHAT_IM_DOING.add(thing)
    return thing


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

    When asking the user to pick a file, this class is used to represent the
    chosen file. It contains metadata about the file, and can also be used to
    access the file's contents.

    Be careful when running your app as a website, since files will need to be
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
        # TODO: Files are currently read in their entirety, immediately. Change
        # that so that they are only fetched once this function is called.
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

        `UnicodeDecodeError`: If the file could not be decoded using the given
            `encoding`.
        """
        return self._contents.decode(encoding)

    @t.overload
    async def open(self, type: t.Literal["r"]) -> StringIO: ...

    @t.overload
    async def open(self, type: t.Literal["rb"]) -> BytesIO: ...

    async def open(
        self, type: t.Literal["r", "rb"] = "r"
    ) -> StringIO | BytesIO:
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


T = t.TypeVar("T")
P = t.ParamSpec("P")

EventHandler = t.Callable[P, t.Any | t.Awaitable[t.Any]] | None


def make_url_relative(base: URL, other: URL) -> URL:
    """
    Returns `other` as a relative URL to `base`. Raises a `ValueError` if
    `other` is not a child of `base`.

    This will never generate URLs containing `..`. If those would be needed a
    `ValueError` is raised instead.
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
        except OSError:
            return False


def ensure_valid_port(host: str, port: int | None) -> int:
    if port is None:
        return choose_free_port(host)

    return port


def first_non_none(*values: T | None) -> T:
    """
    Returns the first non-`None` value, or raises a `ValueError` if all values
    are `None`.
    """

    for value in values:
        if value is not None:
            return value

    raise ValueError("At least one value must be non-`None`")


def _repr_build_function(
    build_function: t.Callable[[], rio.Component],
) -> str:
    """
    Return a recognizable name for the provided function such as
    `Component.build`.
    """

    try:
        self = build_function.__self__  # type: ignore
    except AttributeError:
        try:
            return build_function.__qualname__
        except AttributeError:
            return repr(build_function)

    return f"{type(self).__name__}.{build_function.__name__}"


def safe_build(
    build_function: t.Callable[[], rio.Component],
) -> rio.Component:
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
        from rio.components.error_placeholder import ErrorPlaceholder

        placeholder_component = ErrorPlaceholder(
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
        from rio.components.error_placeholder import ErrorPlaceholder

        placeholder_component = ErrorPlaceholder(
            f"`{build_function_repr}` has returned an invalid result",
            f"Build functions must return instances of `rio.Component`, but the result was {build_result!r}",
        )

    # Save the error in the session, for testing purposes
    placeholder_component.session._crashed_build_functions[build_function] = (
        placeholder_component.error_details
    )

    return placeholder_component


def normalize_url(url: rio.URL) -> rio.URL:
    """
    Returns a normalized version of the given URL.

    This returns a new URL instance which is identical to the given URL, but
    with the following guarantees:

    - The URL is lowercase
    - The URL has no trailing slashes
    """
    path = url.path.rstrip("/")
    path = path.lower()
    return url.with_path(path)


def is_python_script(path: Path) -> bool:
    """
    Guesses whether the path points to a Python script, based on the path's file
    extension.
    """
    return path.suffix in (".py", ".pyc", ".pyd", ".pyo", ".pyw")


def normalize_file_type(file_type: str) -> str:
    """
    Converts different file type formats into a common one.

    This function takes various formats of file types, such as file extensions
    (e.g., ".pdf", "PDF", "*.pdf") or MIME types (e.g., "application/pdf"), and
    converts them into a standardized file extension. The result is always
    lowercase and without any leading dots or wildcard characters.

    This is best-effort. If the input type is invalid or unknown, the cleaned
    input may not be accurate.

    ## Examples

    ```py
    >>> standardize_file_type("pdf")
    'pdf'
    >>> standardize_file_type(".PDF")
    'pdf'
    >>> standardize_file_type("*.pdf")
    'pdf'
    >>> standardize_file_type("application/pdf")
    'pdf'
    ```
    """
    # Normalize the input string
    file_type = file_type.lower().strip()

    # If this is a MIME type, guess the extension
    if "/" in file_type:
        guessed_suffix = mimetypes.guess_extension(file_type, strict=False)

        if guessed_suffix is None:
            file_type = file_type.rsplit("/", 1)[-1]
        else:
            file_type = guessed_suffix.lstrip(".")

    # If it isn't a MIME type, convert it to one anyway. Some file types have
    # multiple commonly used extensions. This will always map them to the same
    # one. For example "jpeg" and "jpg" are both mapped to "jpg".
    else:
        guessed_type, _ = mimetypes.guess_type(
            f"file.{file_type}", strict=False
        )

        file_type = file_type.lstrip(".*")

        if guessed_type is not None:
            guessed_type = mimetypes.guess_extension(
                guessed_type,
                strict=False,
            )

            # Yes, this really happens on some systems. For some reason, we can
            # get the type for a suffix, but not the suffix for the same type.
            if guessed_type is not None:
                file_type = guessed_type.lstrip(".")

    # Done
    return file_type


def soft_sort(
    elements: list[T],
    key: t.Callable[[T], int | None],
) -> None:
    """
    Sorts the given list in-place, allowing for `None` values in the key.

    This function tries to match sorting that humans expect when they assign
    positions to only some items. For example, an item with key `0` or `1`
    should be at the start. Likewise, an item with `9999` should be towards the
    end of the list.

    This function places elements with a key at the specified locations. It then
    assigns any leftover items to the remaining positions in the list, in the
    same order they were before sorting.

    Note that there is one special case where this may not work as intended: If
    two items have the same key assigned they obviously cannot be placed at the
    same position. In that case the original order between them is preserved,
    and subsequent items shifted as needed.
    """

    # To ensure we can keep the original order, add the current index to all
    # items.
    keyed_elements = [
        (element, index, key(element)) for index, element in enumerate(elements)
    ]

    # Assign positions to all elements with a provided key. This maps the
    # original index to the assigned position.
    assigned_positions: dict[int, int] = {}

    for _, original_index, key_value in keyed_elements:
        if key_value is None:
            continue

        assigned_positions[original_index] = key_value

    # Assign positions to all other elements
    ii = 0

    for _, original_index, key_value in keyed_elements:
        if key_value is not None:
            continue

        while ii in assigned_positions.values():
            ii += 1

        assigned_positions[original_index] = ii
        ii += 1

    # Sort the elements, taking care to preserve the original order between
    # items with the same key.
    def regular_sort_key(item: tuple[T, int, int | None]) -> tuple[int, int]:
        _, original_index, _ = item
        return assigned_positions[original_index], original_index

    keyed_elements.sort(key=regular_sort_key)

    # Reassign the elements to the original list
    elements.clear()

    for element, _, _ in keyed_elements:
        elements.append(element)
