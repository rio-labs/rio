import asyncio
import json as json_module
import typing as t
import urllib.error
import urllib.parse
import urllib.request
import urllib.response


class HttpError(Exception):
    """
    Raised when an HTTP request fails.

    The status code is `None` if the error wasn't caused by HTTP, but some other
    reason like a network error.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None,
    ) -> None:
        super().__init__(message, status_code)

    @property
    def message(self) -> str:
        return self.args[0]

    @property
    def status_code(self) -> int | None:
        return self.args[1]


class HttpResponse:
    """
    Represents an HTTP response.
    """

    def __init__(
        self,
        *,
        status_code: int,
        headers: dict[str, str],
        content: bytes,
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self._content = content

    def read(self) -> bytes:
        """
        Returns the response body as bytes.
        """
        return self._content

    def json(self) -> t.Any:
        """
        Returns the response body as a JSON object. Raises a
        `json.JSONDecodeError` if the response body is not valid JSON.
        """

        try:
            return json_module.loads(self._content)
        except UnicodeDecodeError:
            raise json_module.JSONDecodeError(
                "The response body is not valid UTF-8",
                "",
                0,
            )


def _request_sync(
    method: t.Literal["get", "post"],
    url: str,
    *,
    content: str | bytes | None = None,
    json: dict[str, t.Any] | None = None,
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    """
    Makes an HTTP request with the specified parameters. Returns the response
    headers and body.
    """
    # Verify the method
    if method not in ("get", "post"):
        raise ValueError("Invalid method")

    # Prepare the request
    req = urllib.request.Request(
        url,
        method=method.upper(),
    )

    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    if json:
        if content is not None:
            raise ValueError("Cannot specify both `content` and `json`")

        content = json_module.dumps(json)

    if content:
        if isinstance(content, str):
            content = content.encode("utf-8")

        req.data = content

    # Make the request
    try:
        with urllib.request.urlopen(req) as response:
            # Check the status code
            if response.status >= 300:
                raise HttpError(
                    response.reason,
                    response.status,
                )

            # Epic success!
            return HttpResponse(
                status_code=response.status,
                headers={
                    key.lower(): value for key, value in response.getheaders()
                },
                content=response.read(),
            )

    except urllib.error.HTTPError as e:
        raise HttpError(
            e.reason,
            e.code,
        ) from None

    except urllib.error.URLError as e:
        raise HttpError(
            str(e.reason),
            None,
        ) from None


async def request(
    method: t.Literal["get", "post"],
    url: str,
    *,
    content: bytes | None = None,
    json: dict[str, t.Any] | None = None,
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    """
    Makes an HTTP request with the specified parameters. Returns the response
    headers and body.
    """

    return await asyncio.to_thread(
        _request_sync,
        method,
        url,
        content=content,
        json=json,
        headers=headers,
    )


async def main() -> None:
    response = await request(
        "get",
        "https://postman-echo.com/get?foo=bar",
    )

    print(response.status_code)
    print(response.headers)
    print(response.json())


if __name__ == "__main__":
    asyncio.run(main())
