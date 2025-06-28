import subprocess
import sys
import typing as t
from pathlib import Path

import rio.utils

PROJECT_ROOT_DIR = rio.utils.PROJECT_ROOT_DIR
INPUT_DIR = PROJECT_ROOT_DIR / "frontend"
OUTPUT_DIR = PROJECT_ROOT_DIR / "rio" / "frontend files"
ASSETS_DIR = OUTPUT_DIR / "assets"


def main() -> None:
    if "--release" in sys.argv:
        mode = "release"
    else:
        mode = "dev"

    build_frontend(mode=mode)


def build_frontend(mode: t.Literal["dev", "release"]) -> None:
    # npx(*"tsc --noEmit".split())  # type check

    if mode == "release":
        extra_args = []
    else:
        extra_args = ["--mode", "development", "--minify", "false"]

    # Build with vite
    npx(
        "vite",
        "build",
        INPUT_DIR,
        "--outDir",
        OUTPUT_DIR,
        "--config",
        PROJECT_ROOT_DIR / "vite.config.mjs",
        # The real base URL is only known at runtime, and may differ for each
        # session. This string here is an intentionally easy-to-replace
        # placeholder.
        "--base",
        "/rio-base-url-placeholder/rio/frontend/",
        "--emptyOutDir",
        *extra_args,
    )


def npx(*args: str | Path) -> None:
    subprocess.run(
        ["npx", *map(str, args)],
        check=True,
        shell=sys.platform == "win32",
    )


if __name__ == "__main__":
    main()
