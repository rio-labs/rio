"""
Implements HTTP byte serving, as per RFC 7233.

Based on a comment here:
https://github.com/tiangolo/fastapi/issues/1240#issuecomment-1055396884
"""

import io
import mimetypes
import typing as t
import warnings
from pathlib import Path

import fastapi
from fastapi import HTTPException

__all__ = [
    "range_requests_response",
]


def range_requests_response(
    request: fastapi.Request,
    data: bytes | Path,
    *,
    media_type: str | None = None,
) -> fastapi.responses.Response:
    """
    Returns a fastapi response which serves the given file, supporting Range
    Requests as per RFC7233 ("HTTP byte serving").

    Returns a 404 if the file does not exist. In this case a warning is also
    shown in the console.
    """

    # Get the file size. This also verifies the file exists.
    if isinstance(data, Path):
        try:
            file_size_in_bytes = data.stat().st_size
        except FileNotFoundError:
            warnings.warn(f"Cannot find file at {data.absolute()}")
            return fastapi.responses.Response(status_code=404)
    else:
        file_size_in_bytes = len(data)

    # Prepare response headers
    headers = {
        "accept-ranges": "bytes",
        "access-control-expose-headers": (
            "content-type, accept-ranges, content-length, content-range, content-encoding"
        ),
    }

    if media_type is None and isinstance(data, Path):
        # There have been issues with JavaScript files because browsers insist
        # on the mime type "text/javascript", but some PCs aren't configured
        # correctly and return "text/plain". So we purposely avoid using
        # `mimetypes.guess_type` for critical files like JavaScript and CSS.
        try:
            suffix = data.suffixes[0]
            media_type = {
                ".js": "text/javascript",
                ".css": "text/css",
            }[suffix]
        except (IndexError, KeyError):
            media_type = mimetypes.guess_type(data, strict=False)[0]

    if media_type is not None:
        headers["content-type"] = media_type

    # Was a specific range requested?
    range_header = request.headers.get("range")
    if range_header is None:
        start = 0
        end = file_size_in_bytes - 1
        headers["content-length"] = str(file_size_in_bytes)
        status_code = fastapi.status.HTTP_200_OK
    else:
        start, end = parse_range_header(range_header, file_size_in_bytes)
        size = end - start + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start}-{end}/{file_size_in_bytes}"
        status_code = fastapi.status.HTTP_206_PARTIAL_CONTENT

    # Construct the response
    return fastapi.responses.StreamingResponse(
        send_bytes_range_requests(data, start, end),
        headers=headers,
        status_code=status_code,
    )


def send_bytes_range_requests(
    data: bytes | Path,
    start: int,
    end: int,
    chunk_size: int = 1024 * 1024 * 16,
) -> t.Iterator[bytes]:
    """
    Send a file in chunks using Range Requests specification RFC7233. `start`
    and `end` are inclusive as per the spec.
    """
    if isinstance(data, Path):
        file_obj = data.open("rb")
    else:
        file_obj = io.BytesIO(data)

    with file_obj:
        file_obj.seek(start)

        remaining = end - start + 1

        while remaining > 0:
            read_size = min(chunk_size, remaining)
            chunk = file_obj.read(read_size)

            yield chunk

            remaining -= len(chunk)


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    try:
        h = range_header.removeprefix("bytes=").split("-")
        start = int(h[0]) if h[0] != "" else 0
        end = int(h[1]) if h[1] != "" else file_size - 1
    except ValueError:
        raise HTTPException(
            fastapi.status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"Invalid request range header (Range: {range_header!r})",
        )

    if start > end or start < 0 or end > file_size - 1:
        raise HTTPException(
            fastapi.status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"Requested range is out of bounds: (Range: [{start},{end}]) (File size: {file_size}B)",
        )

    return start, end
