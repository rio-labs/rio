from __future__ import annotations

import typing as t
from pathlib import Path

from uniserde import JsonDoc
from yarl import URL

from .. import assets
from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = ["PdfViewer"]


@t.final
class PdfViewer(FundamentalComponent):
    """
    Displays a PDF document.

    `PdfViewer` allows you to display PDF documents in your app. This uses the
    browser's built-in PDF viewer, which typically allows scrolling, zooming,
    searching and similar. If the PDF cannot be displayed, e.g. because the
    browser does not support PDF viewing, a download link will be shown instead.

    The document can be loaded from any source supported by Rio's asset system.
    If the document is hosted somewhere, you can provide a `rio.URL` for easy
    access. To display a local file use a `pathlib.Path` object. Finally, if you
    already have the document data in memory you can pass it as a `bytes`
    object.

    Warning: Unlike most components in Rio, the `PdfViewer` component does not
        have a large `natural` size, but instead only displays part of the
        document if allocated to little space.


    ## Attributes

    `pdf`: The PDF document to display.


    ## Examples

    This example will display a PDF document hosted on the web:

    ```python
    rio.PdfViewer(
        rio.URL("https://example.com/document.pdf"),
    )
    ```

    You can also display PDFs from a path:

    ```python
    from pathlib import Path

    rio.PdfViewer(
        Path("example_document.pdf"),
    )
    ```

    You can access the `App`'s assets directory using the `assets` property.
    This will return a `pathlib.Path` object pointing to the assets directory:

    ```python
    rio.PdfViewer(
        Path(self.session.assets / "example_document.pdf"),
        min_width=20,
        min_height=20,
    )
    ```


    ## Metadata

    `experimental`: True
    """

    pdf: Path | URL | bytes

    def __init__(
        self,
        pdf: Path | URL | bytes,
        *,
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 5,
        min_height: float = 5,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ) -> None:
        super().__init__(
            key=key,
            margin=margin,
            margin_x=margin_x,
            margin_y=margin_y,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            min_width=min_width,
            min_height=min_height,
            # MAX-SIZE-BRANCH max_width=max_width,
            # MAX-SIZE-BRANCH max_height=max_height,
            grow_x=grow_x,
            grow_y=grow_y,
            align_x=align_x,
            align_y=align_y,
            # SCROLLING-REWORK scroll_x=scroll_x,
            # SCROLLING-REWORK scroll_y=scroll_y,
            accessibility_role=accessibility_role,
        )

        self.pdf = pdf

    def _get_pdf_asset(self) -> assets.Asset:
        pdf = self.pdf

        if getattr(self, "_pdf_for_cached_asset", None) != pdf:
            self._cached_pdf_asset = assets.Asset.new(
                pdf,
                media_type="application/pdf",
            )
            self._pdf_for_cached_asset = pdf

        return self._cached_pdf_asset

    def _custom_serialize_(self) -> JsonDoc:
        return {
            "pdfUrl": self._get_pdf_asset()._serialize(self.session),
        }


PdfViewer._unique_id_ = "PdfViewer-builtin"
