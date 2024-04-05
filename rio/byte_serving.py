"""
Implements HTTP byte serving, as per RFC 7233.

Based on a comment here:
https://github.com/tiangolo/fastapi/issues/1240#issuecomment-1055396884
"""

from pathlib import Path
from typing import *  # type: ignore

import fastapi
from fastapi import HTTPException

__all__ = [
    "range_requests_response",
]


def send_bytes_range_requests(
    file_obj: BinaryIO,
    start: int,
    end: int,
    chunk_size: int = 16 * 1024 * 1024,
) -> Iterator[bytes]:
    """
    Send a file in chunks using Range Requests specification RFC7233. `start`
    and `end` are inclusive as per the spec.
    """
    with file_obj as f:
        f.seek(start)

        remaining = end - start + 1

        while remaining > 0:
            read_size = min(chunk_size, remaining)
            chunk = f.read(read_size)

            yield chunk

            remaining -= len(chunk)


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    try:
        h = range_header.replace("bytes=", "").split("-")
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


def range_requests_response(
    request: fastapi.Request,
    file_path: Path,
    *,
    media_type: str | None = None,
) -> fastapi.responses.Response:
    """
    Returns a fastapi response which serves the given file, supporting Range
    Requests as per RFC7233 ("HTTP byte serving").

    Returns a 404 if the file does not exist.
    """

    # Get the file size. This also verifies the file exists.
    try:
        file_size_in_bytes = file_path.stat().st_size
    except FileNotFoundError:
        return fastapi.responses.Response(status_code=404)

    # Prepare response headers
    headers = {
        "accept-ranges": "bytes",
        "content-encoding": "identity",
        "content-length": str(file_size_in_bytes),
        "access-control-expose-headers": (
            "content-type, accept-ranges, content-length, content-range, content-encoding"
        ),
    }

    if media_type is not None:
        headers["content-type"] = media_type

    # Was a specific range requested?
    range_header = request.headers.get("range")
    if range_header is None:
        start = 0
        end = file_size_in_bytes - 1
        status_code = fastapi.status.HTTP_200_OK
    else:
        start, end = parse_range_header(range_header, file_size_in_bytes)
        size = end - start + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start}-{end}/{file_size_in_bytes}"
        status_code = fastapi.status.HTTP_206_PARTIAL_CONTENT

    # Construct the response
    return fastapi.responses.StreamingResponse(
        send_bytes_range_requests(file_path.open("rb"), start, end),
        headers=headers,
        status_code=status_code,
    )
