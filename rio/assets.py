from __future__ import annotations

import abc
import hashlib
import io
import os
from pathlib import Path
from typing import *  # type: ignore
from typing_extensions import Self

import httpx
from PIL.Image import Image
from yarl import URL

import rio

from .utils import ImageLike
from .self_serializing import SelfSerializing


def _securely_hash_bytes_changes_between_runs(data: bytes) -> bytes:
    """
    Returns an undefined, cryptographically secure hash of the given bytes.

    The hash *may* change between runs of the program, but should generally be
    quite stable. (Since this is used to generate asset URLs, it's beneficial to
    produce the same URL every time so that browsers can cache the assets.)
    """

    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.digest()


_ASSETS: dict[tuple[bytes | Path | URL, str | None], Asset] = {}


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

    def __init__(
        self,
        media_type: str | None = None,
    ):
        if type(self) is __class__:
            raise Exception(
                "Cannot instantiate Asset directly; use `Asset.new()` instead"
            )

        # The MIME type of the asset
        self.media_type = media_type

    @overload
    @classmethod
    def new(cls, data: bytes, media_type: str | None = None) -> BytesAsset: ...

    @overload
    @classmethod
    def new(cls, data: Path, media_type: str | None = None) -> PathAsset: ...

    @overload
    @classmethod
    def new(cls, data: URL, media_type: str | None = None) -> UrlAsset: ...

    @classmethod
    def new(
        cls,
        data: bytes | Path | URL,
        media_type: str | None = None,
    ) -> Asset:
        key = (data, media_type)
        try:
            return _ASSETS[key]
        except KeyError:
            pass

        if isinstance(data, Path):
            asset = PathAsset(data, media_type)
        elif isinstance(data, URL):
            asset = UrlAsset(data, media_type)
        elif isinstance(data, (bytes, bytearray)):
            asset = BytesAsset(data, media_type)
        elif isinstance(data, str):
            raise TypeError(
                f"Cannot create asset from input {data!r}. Perhaps you meant to"
                f" pass a `pathlib.Path` or `rio.URL`?"
            )
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
    async def try_fetch_as_blob(self) -> tuple[bytes, str | None]:
        """
        Try to fetch the image as blob & media type. Raises a `ValueError` if
        fetching fails.
        """
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Asset):
            return NotImplemented

        if self.media_type != other.media_type:
            return False

        if type(self) != type(other):
            return False

        return self._eq(other)

    @abc.abstractmethod
    def _eq(self, other: Self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def url(self) -> URL:
        """
        Returns the URL at which the asset can be accessed. The URL may or may
        not be relative.
        """
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

    @property
    def url(self) -> URL:
        return URL(f"/rio/asset/temp-{self.secret_id}")

    def _serialize(self, sess: rio.Session) -> str:
        sess._app_server.weakly_host_asset(self)
        return f"/rio/asset/temp-{self.secret_id}"


class BytesAsset(HostedAsset):
    def __init__(
        self,
        data: bytes | bytearray,
        media_type: str | None = None,
    ):
        super().__init__(media_type)

        self.data = data

    def _eq(self, other: BytesAsset) -> bool:
        return self.data == other.data

    async def try_fetch_as_blob(self) -> tuple[bytes, str | None]:
        return self.data, self.media_type

    def _get_secret_id(self) -> str:
        # TODO: Consider only hashing part of the data + media type + size
        # rather than processing everything
        return "b-" + _securely_hash_bytes_changes_between_runs(self.data).hex()


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

    def _eq(self, other: PathAsset) -> bool:
        return self.path == other.path

    async def try_fetch_as_blob(self) -> tuple[bytes, str | None]:
        try:
            return self.path.read_bytes(), self.media_type
        except IOError:
            raise ValueError(f"Could not load asset from {self.path}")

    def _get_secret_id(self) -> str:
        return (
            "f-"
            + _securely_hash_bytes_changes_between_runs(
                str(self.path).encode("utf-8")
            ).hex()
        )


class UrlAsset(Asset):
    def __init__(
        self,
        url: URL,
        media_type: str | None = None,
    ):
        super().__init__(media_type)

        self._url = url

    def _eq(self, other: UrlAsset) -> bool:
        return self.url == other.url

    async def try_fetch_as_blob(self) -> tuple[bytes, str | None]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(str(self._url))

                content_type = response.headers.get("Content-Type")
                if content_type is None:
                    content_type = "application/octet-stream"
                else:
                    content_type, _, _ = content_type.partition(";")

                return response.read(), content_type
        except httpx.HTTPError:
            raise ValueError(f"Could not fetch asset from {self._url}")

    @property
    def url(self) -> URL:
        return self._url

    def _serialize(self, sess: rio.Session) -> str:
        return self._url.human_repr()


def detect_important_image_types(image: ImageLike) -> str | None:
    if isinstance(image, Path):
        if image.suffix == ".svg":
            return "image/svg+xml"

    if isinstance(image, bytes):
        if b"<svg" in image:
            return "image/svg+xml"

    return None
