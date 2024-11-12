"""
A teeny-weeny synchronous/asynchronous HTTP library. This is not intended to
rival `httpx` or `aiohttp`, but rather to provide a simple interface and be
small. Use it if you just need to make the occasional HTTP request and don't
want to depend on a large library.
"""

import asyncio
import json as json_module
import ssl
import typing as t
import urllib.error
import urllib.request

# Re-export JSONDecodeError, since it can be raised by this module
from json import JSONDecodeError as JSONDecodeError

__all__ = [
    "HttpError",
    "HttpResponse",
    "JSONDecodeError",
    "request",
    "request_sync",
]


HttpMethod = t.Literal[
    "get",
    "GET",
    "head",
    "HEAD",
    "options",
    "OPTIONS",
    "trace",
    "TRACE",
    "put",
    "PUT",
    "delete",
    "DELETE",
    "post",
    "POST",
    "patch",
    "PATCH",
    "connect",
    "CONNECT",
]


HTTP_METHOD_VALUES = t.get_args(HttpMethod)


class HttpError(Exception):
    """
    Raised when an HTTP request fails.

    The status code is `None` if the error wasn't caused by HTTP, but some other
    reason like a network error.


    ## Attributes

    `method`: The HTTP method used in the failed request

    `url`: The target URL of the failed request

    `message`: A human-readable error message

    `status_code`: The HTTP status code, if applicable. This will be `None` if
        the error was not caused by HTTP itself, but rather an external issue
        such as missing permissions or a network error.
    """

    def __init__(
        self,
        *,
        method: HttpMethod,
        url: str,
        status_code: int | None,
        message: str,
    ) -> None:
        super().__init__(
            method,
            url,
            status_code,
            message,
        )

    @property
    def method(self) -> str:
        return self.args[0]

    @property
    def url(self) -> str:
        return self.args[1]

    @property
    def status_code(self) -> int | None:
        return self.args[2]

    @property
    def message(self) -> str:
        return self.args[3]


class HttpResponse:
    """
    Represents the response received by a server after making an HTTP request.


    ## Attributes

    `status_code`: The HTTP status code of the response

    `headers`: A dictionary of headers received in the response. These are all
        lowercase so you can access them without worrying about casing.
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
        Returns the response body as a JSON object.


        ## Raises

        `json.JSONDecodeError`: If the response body is not valid JSON. To
            simplify your error handling, this will also consider invalid UTF-8
            to be invalid JSON. (Which is in line with the JSON spec, which
            requires all JSON documents to be encoded in UTF-8.)
        """

        try:
            return json_module.loads(self._content)
        except UnicodeDecodeError:
            raise json_module.JSONDecodeError(
                "The response body is not valid UTF-8",
                "",
                0,
            )


def request_sync(
    method: HttpMethod,
    url: str,
    *,
    content: str | bytes | None = None,
    json: dict[str, t.Any] | None = None,
    headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
) -> HttpResponse:
    """
    Makes a synchronous HTTP request with the specified parameters, returning
    the response. Prefer using the asynchronous `request` function instead.


    ## Parameters

    `method`: What sort of HTTP request to make

    `url`: The URL to make the request to

    `content`: The body of the request, as either a string or bytes. May be
        `None` to make a request without a body.

    `json`: Convenience parameter to specify the body of the request as a JSON
        object. This will also change the `content-type` header to
        `"application/json"`. If this parameter is specified, `content` must be
        `None`.

    `headers`: Additional headers to include in the request. Any headers
        provided here will override the default headers.

    `verify_ssl`: Whether to verify the SSL certificate of the server.


    ## Raises

    `ValueError`: If the `method` is not one of `"get"` or `"post"`

    `HttpError`: If the request fails for any reason. This includes external
        errors such as network issues, as well as any non-200 status codes.
    """
    # Verify the method
    if method not in HTTP_METHOD_VALUES:
        raise ValueError("Invalid method")

    # Prepare a set of default headers
    all_headers = {
        "user-agent": "rio.arequests/0.1",
        "content-type": "application/octet-stream",
    }

    # Prepare the request
    req = urllib.request.Request(
        url,
        method=method.upper(),
    )

    # If a JSON object was provided, use it as content and also set the
    # content-type header
    if json:
        if content is not None:
            raise ValueError("Cannot specify both `content` and `json`")

        content = json_module.dumps(json)
        all_headers["content-type"] = "application/json"

    # If content was provided add it to the request
    if content:
        if isinstance(content, str):
            content = content.encode("utf-8")

        req.data = content

    # Add the headers
    #
    # User-provided headers override the default headers. Take care to do this
    # late so that the logic above (e.g. JSON) can modify the default headers.
    if headers:
        for header, value in headers.items():
            all_headers[header.lower()] = value

    for key, value in all_headers.items():
        req.add_header(key, value)

    # Prepare the SSL context
    #
    # The default context verifies SSL. If that is not desired, override it.
    if verify_ssl:
        ssl_context = None
    else:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    # Make the request
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            # Check the status code
            if response.status >= 300:
                raise HttpError(
                    method=method,
                    url=url,
                    status_code=response.status,
                    message=response.reason,
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
            method=method,
            url=url,
            status_code=e.code,
            message=e.reason,
        ) from None

    except urllib.error.URLError as e:
        raise HttpError(
            method=method,
            url=url,
            status_code=None,
            message=str(e.reason),
        ) from None


async def request(
    method: HttpMethod,
    url: str,
    *,
    content: bytes | None = None,
    json: dict[str, t.Any] | None = None,
    headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
) -> HttpResponse:
    """
    Makes an asynchronous HTTP request with the specified parameters, returning
    the response.


    ## Parameters

    `method`: What sort of HTTP request to make

    `url`: The URL to make the request to

    `content`: The body of the request, as either a string or bytes. May be
        `None` to make a request without a body.

    `json`: Convenience parameter to specify the body of the request as a JSON
        object. If this is specified, `content` must be `None`.

    `headers`: Additional headers to include in the request. Any headers
        provided here will override the default headers.

    `verify_ssl`: Whether to verify the SSL certificate of the server.


    ## Raises

    `ValueError`: If the `method` is not one of `"get"` or `"post"`

    `HttpError`: If the request fails for any reason. This includes external
        errors such as network issues, as well as any non-200 status codes.
    """

    return await asyncio.to_thread(
        request_sync,
        method,
        url,
        content=content,
        json=json,
        headers=headers,
        verify_ssl=verify_ssl,
    )
