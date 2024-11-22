import io
import tempfile
import typing as t

import pytest

import rio.utils

ASCII_BYTES = (b"Hello, World!", "Hello, World!")
UTF8_BYTES = (b"\xe2\x98\x83", "☃")  # Snowman
LATIN1_BYTES = (b"\xa9", "©")  # Copyright symbol
BLOB_BYTES = (b"\x80\x80", None)  # Invalid ASCII and UTF-8


def create_blobs_variants(blob: bytes) -> t.Iterable[bytes | t.IO[bytes]]:
    """
    Given a bytes object, return it in several variants:

    - As a bytes object
    - As in-memory stream (io.BytesIO)
    - As a real file (tempfile.NamedTemporaryFile)
    """

    # In-memory bytes object
    yield blob

    # A stream
    yield io.BytesIO(blob)

    # A real friggin file
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(blob)
    f.seek(0)
    yield f


def make_test_blobs() -> (
    t.Iterable[
        tuple[
            bytes,
            bytes | t.IO[bytes],
        ]
    ]
):
    """
    Generate a variety of blobs to use as file contents, in different forms.
    """

    blobs = [
        ASCII_BYTES[0],
        UTF8_BYTES[0],
        LATIN1_BYTES[0],
        BLOB_BYTES[0],
    ]

    for as_bytes in blobs:
        for as_some_blob in create_blobs_variants(as_bytes):
            yield as_bytes, as_some_blob


def make_test_texts() -> (
    t.Iterable[
        t.Tuple[
            bytes | t.IO[bytes],
            str | None,
            str | t.Type[Exception],
        ],
    ]
):
    """
    Generate a variety of blobs to be decoded into strings, in different formats.
    Each entry contains the blob, the encoding to use, and the expected output.
    """
    as_bytes = [
        (
            ASCII_BYTES[0],
            "ascii",
            ASCII_BYTES[1],
        ),
        (
            ASCII_BYTES[0],
            "utf-8",
            ASCII_BYTES[1],
        ),
        (
            UTF8_BYTES[0],
            "ascii",
            UnicodeDecodeError,
        ),
        (
            UTF8_BYTES[0],
            "utf-8",
            UTF8_BYTES[1],
        ),
        (
            LATIN1_BYTES[0],
            "ascii",
            UnicodeDecodeError,
        ),
        (
            LATIN1_BYTES[0],
            "utf-8",
            UnicodeDecodeError,
        ),
        (
            LATIN1_BYTES[0],
            "latin1",
            LATIN1_BYTES[1],
        ),
        (
            BLOB_BYTES[0],
            "ascii",
            UnicodeDecodeError,
        ),
        (
            BLOB_BYTES[0],
            "utf-8",
            UnicodeDecodeError,
        ),
    ]

    # Expand the blobs into multiple formats
    for as_bytes, encoding, expected in as_bytes:
        for as_some_blob in create_blobs_variants(as_bytes):
            yield as_some_blob, encoding, expected


@pytest.mark.parametrize(
    "as_bytes,as_some_blob",
    make_test_blobs(),
)
async def test_read_bytes(
    as_bytes: bytes,
    as_some_blob: bytes | t.IO[bytes],
) -> None:
    """
    Create a `FileInfo`, read back the bytes and make sure the output matches
    the input.
    """

    # Create a FileInfo object
    file_info = rio.utils.FileInfo(
        name="name",
        size_in_bytes=0,
        media_type="application/octet-stream",
        contents=as_some_blob,
    )

    # Read the contents back
    contents_out = await file_info.read_bytes()

    assert as_bytes == contents_out


@pytest.mark.parametrize(
    "as_some_blob,encoding,expected",
    make_test_texts(),
)
async def test_read_text(
    as_some_blob: bytes | t.IO[bytes],
    encoding: str,
    expected: t.Type[Exception] | str,
) -> None:
    """
    Create a `FileInfo`, read back the text and make sure the output matches
    the input, or raises the appropriate exception.
    """

    # Create a FileInfo object
    file_info = rio.utils.FileInfo(
        name="name",
        size_in_bytes=0,
        media_type="application/octet-stream",
        contents=as_some_blob,
    )

    # Try to read the contents back
    if isinstance(expected, str):
        contents_out = await file_info.read_text(encoding=encoding)
        assert contents_out == expected

    else:
        with pytest.raises(expected):
            await file_info.read_text(encoding=encoding)


@pytest.mark.parametrize(
    "as_bytes,as_some_blob",
    make_test_blobs(),
)
async def test_open_bytes(
    as_bytes: bytes,
    as_some_blob: bytes | t.IO[bytes],
) -> None:
    """
    Create a `FileInfo`, open it as a binary file and make sure the output
    matches the input.
    """

    # Create a FileInfo object
    file_info = rio.utils.FileInfo(
        name="name",
        size_in_bytes=0,
        media_type="application/octet-stream",
        contents=as_some_blob,
    )

    # Open the file
    as_file = await file_info.open("rb")
    contents_out = as_file.read()

    assert as_bytes == contents_out


@pytest.mark.parametrize(
    "as_some_blob,encoding,expected",
    make_test_texts(),
)
async def test_open_text(
    as_some_blob: bytes | t.IO[bytes],
    encoding: str,
    expected: t.Type[Exception] | str,
) -> None:
    """
    Create a `FileInfo`, open it as a text file and make sure the output matches
    the input.
    """

    # Create a FileInfo object
    file_info = rio.utils.FileInfo(
        name="name",
        size_in_bytes=0,
        media_type="application/octet-stream",
        contents=as_some_blob,
    )

    # Open the file
    if isinstance(expected, str):
        as_file = await file_info.open("r", encoding=encoding)
        contents_out = as_file.read()
        assert contents_out == expected

    else:
        with pytest.raises(expected):
            as_file = await file_info.open("r", encoding=encoding)
            as_file.read()
