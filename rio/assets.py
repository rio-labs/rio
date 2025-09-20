from __future__ import annotations

import abc
import hashlib
import io
import os
from pathlib import Path

import platformdirs
import typing_extensions as t
from PIL.Image import Image
from yarl import URL

import rio
import rio.arequests as arequests

from .self_serializing import SelfSerializing
from .utils import ImageLike


def _securely_hash_bytes_changes_between_runs(
    data: bytes | bytearray,
) -> bytes:
    """
    Returns an undefined, cryptographically secure hash of the given bytes.

    The hash *may* change between runs of the program, but should generally be
    quite stable. (Since this is used to generate asset URLs, it's beneficial to
    produce the same URL every time so that browsers can cache the assets.)
    """

    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.digest()


_ASSETS: dict[tuple[bytes | str | Path | URL, str | None], Asset] = {}

CACHE_DIR = platformdirs.user_cache_path(
    appname="rio", appauthor="rio-labs", ensure_exists=True
)


class Asset(SelfSerializing):
    """
    Base class for assets - i.e. files that the client needs to be able to
    access. Assets can be hosted locally or remotely.

    Assets are "singletons", i.e. if you create two assets with the same input,
    they will be the same object:

    ```python
    >>> Asset.new(Path("foo.png")) is Asset.new(Path("foo.png"))
    True
    ```

    To use an asset in a component, simply store it in the component's state. The
    asset will automatically register itself with the AppServer (if necessary)
    and serialize itself as a URL.
    """

    def __init__(self, media_type: str | None = None):
        # The MIME type of the asset
        self.media_type = media_type

    @t.overload
    @staticmethod
    def new(
        data: bytes | str | Path,
        media_type: str | None = None,
        *,
        allow_str: bool = False,
        rehost: bool = False,
        cache_locally: bool = False,
    ) -> HostedAsset: ...

    @t.overload
    @staticmethod
    def new(
        data: bytes | str | Path | URL,
        media_type: str | None = None,
        *,
        allow_str: bool = False,
        rehost: t.Literal[True],
        cache_locally: bool = False,
    ) -> HostedAsset: ...

    @t.overload
    @staticmethod
    def new(
        data: bytes | str | Path | URL,
        media_type: str | None = None,
        *,
        allow_str: bool = False,
        rehost: bool = False,
        cache_locally: bool = False,
    ) -> Asset: ...

    @staticmethod
    def new(
        data: bytes | str | Path | URL,
        media_type: str | None = None,
        *,
        allow_str: bool = False,
        rehost: bool = False,
        cache_locally: bool = False,
    ) -> Asset:
        key = (data, media_type)
        try:
            return _ASSETS[key]
        except KeyError:
            pass

        if isinstance(data, Path):
            asset = PathAsset(data, media_type)
        elif isinstance(data, URL):
            if rehost:
                asset = RehostedUrlAsset(
                    data, media_type, cache_locally=cache_locally
                )
            else:
                asset = UrlAsset(data, media_type, cache_locally=cache_locally)
        elif isinstance(data, (bytes, bytearray)):
            asset = BytesAsset(data, media_type)
        elif isinstance(data, str):
            if not allow_str:
                raise TypeError(
                    f"Cannot create asset from input {data!r}. Perhaps you"
                    f" meant to pass a `pathlib.Path` or `rio.URL`?"
                )

            asset = StringAsset(data, media_type)
        else:
            raise TypeError(f"Cannot create asset from input {data!r}")

        _ASSETS[key] = asset
        return asset

    @classmethod
    def from_image(
        cls,
        image: ImageLike,
        media_type: str | None = None,
    ) -> Asset:
        if isinstance(image, Image):
            file = io.BytesIO()
            image.save(file, format="PNG")
            image = file.getvalue()
            media_type = "image/png"
        elif media_type is None:
            # For some image formats, browsers are too stupid to display the
            # image correctly if we don't explicitly tell them the mime type.
            # Check for those formats.
            media_type = detect_important_image_types(image)

        return Asset.new(image, media_type)

    @abc.abstractmethod
    async def fetch_as_bytes(self) -> bytes | bytearray:
        """
        Try to fetch the file as blob & media type. Raises a `ValueError` if
        fetching fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_as_text(self) -> str:
        """
        Try to fetch the file as text. Raises a `ValueError` if fetching fails.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError

    def _eq(self, other: object) -> t.TypeGuard[t.Self]:
        if not isinstance(other, type(self)):
            return False

        if self.media_type != other.media_type:
            return False

        return True

    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def _serialize(self, sess: rio.Session) -> str:
        """
        Make sure this asset is available under its URL, and return that URL,
        unescaped.
        """
        raise NotImplementedError


class HostedAsset(Asset):
    """
    Base class for assets that are hosted locally.
    """

    @property
    def secret_id(self) -> str:
        # The asset's id both uniquely identifies the asset, and is used as part
        # of the asset's URL.
        #
        # It is derived from the data, so that if the same file is to be hosted
        # multiple times only one instance is actually stored. Furthermore, this
        # allows the client to cache the asset efficiently, since the URL is
        # always the same.
        try:
            return self._secret_id
        except AttributeError:
            pass

        self._secret_id = self._get_secret_id()
        return self._secret_id

    @abc.abstractmethod
    def _get_secret_id(self) -> str:
        raise NotImplementedError

    def __hash__(self) -> int:
        return hash(self.secret_id)

    def __eq__(self, other: object) -> bool:
        return self._eq(other) and self.secret_id == other.secret_id

    def _serialize(self, sess: rio.Session) -> str:
        return str(sess._app_server.weakly_host_asset(self))


class BytesAsset(HostedAsset):
    def __init__(
        self,
        data: bytes | bytearray,
        media_type: str | None = None,
    ):
        super().__init__(media_type)

        self.data = data

    async def fetch_as_bytes(self) -> bytes | bytearray:
        return self.data

    async def fetch_as_text(self) -> str:
        return self.data.decode("utf-8")

    def _get_secret_id(self) -> str:
        # TODO: Consider only hashing part of the data + media type + size
        # rather than processing everything
        return "b-" + _securely_hash_bytes_changes_between_runs(self.data).hex()

    def __repr__(self) -> str:
        max_bytes = 50
        if len(self.data) <= max_bytes:
            data_repr = repr(self.data)
        else:
            data_repr = repr(self.data[:max_bytes]) + "..."

        return f"<BytesAsset of size {len(self.data)} {data_repr}>"


class StringAsset(HostedAsset):
    def __init__(
        self,
        data: str,
        media_type: str | None = None,
    ):
        super().__init__(media_type)

        self.data = data

    async def fetch_as_bytes(self) -> bytes | bytearray:
        return self.data.encode()

    async def fetch_as_text(self) -> str:
        return self.data

    def _get_secret_id(self) -> str:
        # TODO: Consider only hashing part of the data + media type + size
        # rather than processing everything
        return (
            "s-"
            + _securely_hash_bytes_changes_between_runs(
                self.data.encode()
            ).hex()
        )

    def __repr__(self) -> str:
        max_chars = 50
        if len(self.data) <= max_chars:
            data_repr = repr(self.data)
        else:
            data_repr = repr(self.data[:max_chars]) + "..."

        return f"<StringAsset of size {len(self.data)} {data_repr}>"


class PathAsset(HostedAsset):
    def __init__(
        self,
        path: os.PathLike | str,
        media_type: str | None = None,
    ):
        super().__init__(media_type)

        # Note: The path doesn't have to point to an existing file. Files can be
        # created and deleted at any time, so we have to handle that situation
        # gracefully anyway.
        self.path = Path(path)

    async def fetch_as_bytes(self) -> bytes:
        try:
            return self.path.read_bytes()
        except IOError:
            raise ValueError(f"Could not load asset from {self.path}")

    async def fetch_as_text(self) -> str:
        try:
            return self.path.read_text("utf-8")
        except (IOError, UnicodeDecodeError):
            raise ValueError(f"Could not load asset from {self.path} as text")

    def _get_secret_id(self) -> str:
        return (
            "f-"
            + _securely_hash_bytes_changes_between_runs(
                str(self.path).encode("utf-8")
            ).hex()
        )

    def __repr__(self) -> str:
        return f'<PathAsset "{self.path}">'


class UrlAsset(Asset):
    def __init__(
        self,
        url: URL,
        media_type: str | None = None,
        *,
        cache_locally: bool = False,
    ):
        super().__init__(media_type)

        self._url = url
        self._cache_locally = cache_locally

        if cache_locally:
            file_name = hashlib.sha256(str(self._url).encode()).hexdigest()
            self.local_cache_path = CACHE_DIR / file_name
        else:
            self.local_cache_path = None

    async def fetch_as_bytes(self) -> bytes:
        data, encoding = await self._fetch()
        return data

    async def fetch_as_text(self) -> str:
        data, encoding = await self._fetch()

        if encoding is None:
            encoding = "utf8"

        return data.decode(encoding)

    async def _fetch(self) -> tuple[bytes, str | None]:
        cache_path = self.local_cache_path

        if cache_path is None:
            return await self._fetch_from_internet()

        try:
            data = cache_path.read_bytes()
        except FileNotFoundError:
            data, encoding = await self._fetch_from_internet()
            cache_path.write_bytes(data)
        else:
            encoding = None

        return data, encoding

    async def _fetch_from_internet(
        self,
    ) -> tuple[bytes, str | None]:
        try:
            response = await arequests.request("get", str(self._url))
        except arequests.HttpError:
            raise ValueError(f"Could not fetch asset from {self._url}")

        encoding = response.headers.get("content-type")
        if encoding:
            _, _, encoding = encoding.partition("charset=")

            if not encoding:
                encoding = None

        return response.read(), encoding

    @property
    def url(self) -> URL:
        return self._url

    def __hash__(self) -> int:
        return hash(self._url)

    def __eq__(self, other: object) -> bool:
        return self._eq(other) and self._url == other._url

    def _serialize(self, sess: rio.Session) -> str:
        return self._url.human_repr()

    def __repr__(self) -> str:
        return f'<UrlAsset "{self._url.human_repr()}">'


class RehostedUrlAsset(HostedAsset, UrlAsset):
    def _get_secret_id(self) -> str:
        bytes_url = str(self._url).encode()
        return "u-" + _securely_hash_bytes_changes_between_runs(bytes_url).hex()


def detect_important_image_types(image: ImageLike) -> str | None:
    if isinstance(image, Path):
        if image.suffix == ".svg":
            return "image/svg+xml"

    if isinstance(image, bytes):
        if b"<svg" in image:
            return "image/svg+xml"

    return None
