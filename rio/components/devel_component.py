from __future__ import annotations

import concurrent.futures
import dataclasses
import subprocess
import tempfile
import typing as t
from pathlib import Path

import rio

from .component import AccessibilityRole, Key
from .fundamental_component import FundamentalComponent

__all__ = [
    "DevelComponent",
]

_SOURCE_DIRECTORY: Path | None = None

_CSS_SOURCE: str = ""
_JS_SOURCE: str = ""


class DevelComponent(FundamentalComponent):
    """
    TODO

    ## Metadata

    `public`: False
    """

    children: t.Sequence[rio.Component] = dataclasses.field(
        default_factory=list
    )

    def __init__(
        self,
        *,
        children: t.Iterable[rio.Component],
        key: Key | None = None,
        margin: float | None = None,
        margin_x: float | None = None,
        margin_y: float | None = None,
        margin_left: float | None = None,
        margin_top: float | None = None,
        margin_right: float | None = None,
        margin_bottom: float | None = None,
        min_width: float = 0,
        min_height: float = 0,
        # MAX-SIZE-BRANCH max_width: float | None = None,
        # MAX-SIZE-BRANCH max_height: float | None = None,
        grow_x: bool = False,
        grow_y: bool = False,
        align_x: float | None = None,
        align_y: float | None = None,
        # SCROLLING-REWORK scroll_x: t.Literal["never", "auto", "always"] = "never",
        # SCROLLING-REWORK scroll_y: t.Literal["never", "auto", "always"] = "never",
        accessibility_role: AccessibilityRole | None = None,
    ):
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

        self.children = list(children)

    @classmethod
    def initialize(cls, directory_path: Path):
        global _SOURCE_DIRECTORY, _CSS_SOURCE, _JS_SOURCE

        # Make sure the component is only initialized once
        if _SOURCE_DIRECTORY is not None:
            raise RuntimeError("DevelComponent is already initialized")

        # Keep track of the source directory
        _SOURCE_DIRECTORY = directory_path

        assert _SOURCE_DIRECTORY.exists(), (
            "`DevelComponent` source directory does not exist"
        )
        assert _SOURCE_DIRECTORY.is_dir(), (
            "`DevelComponent` source directory is not a directory"
        )

        # Find the input files
        scss_path = _SOURCE_DIRECTORY / "styles.scss"
        ts_path = _SOURCE_DIRECTORY / "script.ts"

        if not scss_path.exists():
            raise RuntimeError(
                "Missing `styles.scss` in `DevelComponent` source directory"
            )

        if not ts_path.exists():
            raise RuntimeError(
                "Missing `script.ts` in `DevelComponent` source directory"
            )

        # Compile the two, in parallel
        print("DevelComponent: Compiling `DevelComponent` component source")
        css_path = Path(
            tempfile.NamedTemporaryFile(suffix=".css", delete=False).name
        )
        js_path = Path(
            tempfile.NamedTemporaryFile(suffix=".js", delete=False).name
        )

        tasks = [
            ("sass", str(scss_path), str(css_path)),
            (
                "tsc",
                "--lib",
                "dom,es6",
                str(ts_path),
                "--target",
                "ES6",
                "--outFile",
                str(js_path),
            ),
        ]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for task in tasks:
                executor.submit(subprocess.run, task, check=True)

        # Read the source files
        assert css_path.exists(), "Sass compilation failed"
        print(f"DevelComponent: The compiled CSS is at {css_path}")

        assert js_path.exists(), "Typescript compilation failed"
        print(f"DevelComponent: The compiled JS is at {js_path}")

        _CSS_SOURCE = css_path.read_text()
        _JS_SOURCE = js_path.read_text()

    @classmethod
    def build_javascript_source(cls, sess: rio.Session) -> str:
        if _SOURCE_DIRECTORY is None:
            raise RuntimeError("`DevelComponent` is not initialized")

        return _JS_SOURCE

    @classmethod
    def build_css_source(cls, sess: rio.Session) -> str:
        if _SOURCE_DIRECTORY is None:
            raise RuntimeError("`DevelComponent` is not initialized")

        return _CSS_SOURCE
