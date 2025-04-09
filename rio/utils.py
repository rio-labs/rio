from __future__ import annotations

import dataclasses
import hashlib
import io
import mimetypes
import os
import re
import secrets
import socket
import typing as t
from io import BytesIO, StringIO
from pathlib import Path

import imy.assets
import typing_extensions as te
from PIL.Image import Image
from yarl import URL

import rio

from . import deprecations

__all__ = [
    "EventHandler",
    "FileInfo",
    "ImageLike",
    "escape_markdown",
    "escape_markdown_code",
    "i_know_what_im_doing",
]


T = t.TypeVar("T")
P = t.ParamSpec("P")

EventHandler = t.Callable[P, t.Any | t.Awaitable[t.Any]] | None


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
    """
    Suppresses warnings about likely mistakes.

    This is a function/class decorator that suppresses certain warnings telling
    you that you likely made a mistake.

    ## Parameters

    `thing`: The function or class to suppress.
    """
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


@dataclasses.dataclass(frozen=True)
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
    _contents: bytes | t.IO[bytes] = dataclasses.field(repr=False)

    def __init__(
        self,
        name: str,
        size_in_bytes: int,
        media_type: str,
        contents: bytes | t.IO[bytes],
    ) -> None:
        """
        Initializes a new `FileInfo` instance.

        This function creates a new `FileInfo` object. You'll usually receive
        these from Rio, rather than having to create them yourself. If you want
        the `FilePickerArea` to display some files without the user having to
        pick them, creating these objects manually can be useful.

        ## Parameters

        `name`: The full name of the file, including the extension.

        `size_in_bytes`: How many bytes the file contains.

        `media_type`: The MIME type of the file, for example `text/plain` or
            `image/png`.

        `contents`: The data stored in the file. This can either be the full
            contents, already read as `bytes`, or a file-like object that Rio
            can read from.
        """
        vars(self).update(
            name=name,
            size_in_bytes=size_in_bytes,
            media_type=media_type,
            _contents=contents,
        )

    @classmethod
    def _from_path(cls, path_str: str) -> te.Self:
        path = Path(path_str)

        media_type = (
            mimetypes.guess_type(path_str, strict=False)[0]
            or "application/octet-stream"
        )

        return cls(
            path.name,
            path.stat().st_size,
            media_type,
            path.open("rb"),
        )

    async def read_bytes(self) -> bytes:
        """
        Asynchronously reads the entire file as `bytes`.

        Reads and returns the entire file as a `bytes` object. If you know that
        the file is text, consider using `read_text` instead.

        ## Raises

        `IOError`: If anything goes wrong while reading the file.
        """
        # If the contents are already bytes, return them as-is
        contents = self._contents

        if isinstance(contents, bytes):
            return contents

        # Why on earth this cast necessary?! How does it suddenly turn into a
        # bytearray or a memoryview?!
        contents = t.cast(t.IO[bytes], self._contents)

        # Otherwise read them, taking care to convert any exceptions to
        # `IOError`.
        try:
            return contents.read()
        except Exception as err:
            raise IOError(str(err)) from err
        finally:
            contents.close()

    async def read_text(self, *, encoding: str = "utf-8") -> str:
        """
        Asynchronously reads the entire file as text.

        Reads and returns the entire file as a `str` object. The file is decoded
        using the given `encoding`. If you don't know that the file is valid
        text, use `read_bytes` instead.


        ## Parameters

        encoding: The encoding to use when decoding the file.


        ## Raises

        `IOError`: If anything goes wrong while reading the file.

        `UnicodeDecodeError`: If the file could not be decoded using the given
            `encoding`.
        """
        # Get the contents as bytes
        as_bytes = await self.read_bytes()

        # Decode them
        return as_bytes.decode(encoding)

    @t.overload
    async def open(
        self,
        type: t.Literal["r"],
        *,
        encoding: str = "utf-8",
    ) -> t.IO[str]: ...

    @t.overload
    async def open(
        self,
        type: t.Literal["rb"],
    ) -> t.IO[bytes]: ...

    async def open(
        self,
        type: t.Literal["r", "rb"] = "r",
        *,
        encoding: str = "utf-8",
    ) -> t.IO:
        """
        Asynchronously opens the file, as though it were a regular file on this
        device.

        Opens and returns the file as a file-like object. If 'r' is specified,
        the file is opened as text. If 'rb' is specified, the file is opened as
        bytes.

        Returns a file-like object containing the file's contents.


        ## Parameters

        `type`: The mode to open the file in. 'r' for text, 'rb' for bytes.

        `encoding`: The text encoding to use. Only applicable in 'r' mode.


        ## Raises

        `ValueError`: If the given `type` is not 'r' or 'rb'.

        `IOError`: If anything goes wrong while accessing the file.

        `UnicodeDecodeError`: If the file could not be decoded using the given
            `encoding`.
        """
        # Bytes
        if type == "rb":
            if isinstance(self._contents, bytes):
                return BytesIO(self._contents)

            # Why on earth this cast necessary?! How does it suddenly turn into a
            # bytesarray or a memoryview?!
            return t.cast(t.IO[bytes], self._contents)

        # UTF
        if type == "r":
            if isinstance(self._contents, bytes):
                # Decode the bytes, propagating any `UnicodeDecodeError`
                as_str = self._contents.decode(encoding)

                # Return a file-like object
                return StringIO(as_str)

            return io.TextIOWrapper(
                # Why on earth this cast necessary?! How does it suddenly turn
                # into a bytesarray or a memoryview?!
                t.cast(t.IO[bytes], self._contents),
                encoding=encoding,
            )

        # Invalid
        raise ValueError("Invalid type. Expected 'r' or 'rb'.")


def url_relative_to_base(base: URL, other: URL) -> URL:
    """
    Returns `other` as a relative URL to `base`. Raises a `ValueError` if
    `other` is not a child of `base`. This will never generate URLs containing
    `..`. If those would be needed a `ValueError` is raised instead.

    ## Casing

    The scheme and host are case insensitive, as by the URL standard. The path
    is case sensitive, but a warning will be logged should that be the only
    reason two URLs are not considered equal.
    """
    # Verify the URLs have the same scheme and host
    if base.scheme.lower() != other.scheme.lower():
        raise ValueError(
            f'URLs have different schemes: "{base.scheme}" and "{other.scheme}"'
        )

    base_host = None if base.host is None else base.host.lower()
    other_host = None if other.host is None else other.host.lower()

    if base_host != other_host:
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
    for base_part, other_part in zip(base_parts, other_parts):
        if base_part != other_part:
            # Log a warning if the only difference is casing
            if base_part.lower() == other_part.lower():
                message = f"`{base}` is not considered a base URL of `{other}`, because the URL paths are cased differently. This is considered a different, as by the URL specification. If you were trying to navigate to your own site and it didn't pick this up check your spelling."
                raise ValueError(message)

            raise ValueError(
                f"`{base}` is not a base URL of `{other}`. The paths differ at `{base_part}` and `{other_part}`"
            )

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
    build_function: t.Callable[P, rio.Component],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> rio.Component:
    """
    Calls a build function and returns its result. This differs from just
    calling the function directly, because it catches any exceptions and returns
    a placeholder component instead. It will also ensure the returned value is
    in fact a component.
    """

    # Build the component
    try:
        build_result = build_function(*args, **kwargs)

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

        logging_message = (
            f"The output of `build` methods must be instances of `rio.Component`,"
            f" but `{build_function_repr}` returned `{build_result!r}`"
        )
        gui_message = (
            f"Build functions must return instances of `rio.Component`, but the"
            f" result was {build_result!r}"
        )

        if (
            type(build_result) is tuple
            and len(build_result) == 1
            and isinstance(build_result[0], rio.Component)
        ):
            extra_info = (
                ". You likely have a trailing comma in your return statement,"
                " which is creating a 1-element tuple."
            )

            logging_message += extra_info
            gui_message += extra_info

        rio._logger.error(logging_message)

        # Screw circular imports
        from rio.components.error_placeholder import ErrorPlaceholder

        placeholder_component = ErrorPlaceholder(
            f"`{build_function_repr}` has returned an invalid result",
            gui_message,
        )

    # Save the error in the session, for testing purposes
    placeholder_component.session._crashed_build_functions[build_function] = (
        placeholder_component.error_details
    )

    return placeholder_component


def is_python_script(path: Path) -> bool:
    """
    Guesses whether the path points to a Python script, based on the path's file
    extension.
    """
    return path.suffix in (".py", ".pyc", ".pyd", ".pyo", ".pyw")


def normalize_file_extension(suffix: str) -> str:
    """
    Brings different notations for file extensions into the same form.

    This function takes various formats of file extension and converts them into
    a standardized one. The result is always lowercase and without any leading
    dots or wildcard characters.

    For historical reasons, MIME types are also accepted, but will raise a
    deprecation warning.


    ## Examples

    ```py
    >>> standardize_file_type("pdf")
    "pdf"
    >>> standardize_file_type(".PDF")
    "pdf"
    >>> standardize_file_type("*.pdf")
    "pdf"
    >>> standardize_file_type("application/pdf")  # Deprecated
    "pdf"
    ```
    """
    # Perform some basic normalization
    suffix = suffix.lower().strip()

    # If this is a mime type, run old-school logic
    if "/" in suffix:
        deprecations.warn(
            "MIME types are no longer accepted as allowed file types. Please use file extension instead (e.g. `.pdf` instead of `application/pdf`).",
            since="0.10.10",
        )

        guessed_suffix = mimetypes.guess_extension(suffix, strict=False)

        if guessed_suffix is None:
            return suffix.rsplit("/", 1)[-1]
        else:
            return guessed_suffix.lstrip(".")

    # Remove any leading dots or wildcards
    suffix = suffix.lstrip(".*")

    # Done
    return suffix


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


def verify_and_interpolate_gradient_stops(
    raw_stops: t.Iterable[rio.Color | tuple[rio.Color, float]],
) -> list[tuple[rio.Color, float]]:
    """
    Gradient stops can be provided either as just colors, or colors, or colors
    with a specific position in the gradient. This function normalizes the input
    so that every stop has both color and position.

    - The first and last stop - if not specified - will have positions of 0 and
      1 respectively.
    - All other missing positions will be linearly interpolated

    This also makes sure that:

    - there is at least one stop
    - no explicit stop position is outside the range [0, 1]
    - all explicitly provided stops are ascending

    Finally, the result is guaranteed to have one stop at position 0 and one at
    position 1.

    ## Raises

    `ValueError`: If any of the above conditions are not met.
    """
    # Make sure we can index into the iterable and iterate over it as often as
    # we'd like
    stops = list(raw_stops)

    # Make sure we got at least one stop
    if not stops:
        raise ValueError("Gradients must have at least one stop")

    # Inserting stops shifts the indices relative to what the user expects.
    # Account for that.
    user_index_shift = 0

    # Make sure there is a stop at position 0
    if not isinstance(stops[0], tuple):
        first_stop: rio.Color = stops.pop(0)  # type: ignore
        stops.insert(0, (first_stop, 0.0))
    elif stops[0][1] != 0.0:
        stops.insert(0, (stops[0][0], 0.0))
        user_index_shift = -1

    # Make sure there is a stop at position 1
    if not isinstance(stops[-1], tuple):
        last_stop: rio.Color = stops.pop()  # type: ignore
        stops.append((last_stop, 1.0))
    elif stops[-1][1] != 1.0:
        stops.append((stops[-1][0], 1.0))

    # Stop 0 needs a separate position check because the loop below only checks
    # the right hand side of each stop range
    first_stop_pos = stops[0][1]  # type: ignore

    if not 0 <= first_stop_pos <= 1:  # type: ignore
        raise ValueError(
            f"Gradient stop positions must be in range [0, 1], but stop 0 is at position {first_stop_pos}"
        )

    # Walk the stops, interpolating positions as needed
    prev_positioned_index: int = 0

    def interpolate_stops_and_verify_ascending_position(
        left_positioned_ii: int,
        right_positioned_ii: int,
    ) -> None:
        assert right_positioned_ii > left_positioned_ii
        left_pos = stops[left_positioned_ii][1]  # type: ignore
        right_pos = stops[right_positioned_ii][1]  # type: ignore

        # Make sure the positions are ascending
        if left_pos > right_pos:
            raise ValueError(
                f"Gradient stops must be in ascending order, but stop {left_positioned_ii + user_index_shift} is at position {left_pos} while stop {right_positioned_ii + user_index_shift} is at position {right_pos}"
            )

        # Interpolate all latent stops
        step_size = (right_pos - left_pos) / (
            right_positioned_ii - left_positioned_ii
        )
        cur_pos = left_pos + step_size

        for ii in range(left_positioned_ii + 1, right_positioned_ii):
            color: rio.Color = stops[ii]  # type: ignore
            stops[ii] = (color, cur_pos)
            cur_pos += step_size

    for ii in range(1, len(stops)):
        # Get the current stop
        stop = stops[ii]

        # If this stop is not positioned, skip it for now
        if not isinstance(stop, tuple):
            continue

        # It is positioned
        #
        # Make sure it's in range [0, 1]
        if not 0 <= stop[1] <= 1:
            raise ValueError(
                f"Gradient stop positions must be in range [0, 1], but stop {ii + user_index_shift} is at position {stop[1]}"
            )

        # interpolate the latent stops
        interpolate_stops_and_verify_ascending_position(
            prev_positioned_index, ii
        )

        # This is the new anchor
        prev_positioned_index = ii

    # Done
    return stops  # type: ignore
