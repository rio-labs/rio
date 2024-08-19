import subprocess
import sys
from pathlib import Path

import rio.utils

PROJECT_ROOT_DIR = rio.utils.PROJECT_ROOT_DIR
INPUT_DIR = PROJECT_ROOT_DIR / "frontend"
OUTPUT_DIR = PROJECT_ROOT_DIR / "rio" / "frontend files"
ASSETS_DIR = OUTPUT_DIR / "assets"


def build(*extra_args: str) -> None:
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


def dev_build() -> None:
    build("--mode", "development", "--minify", "false")


def npx(*args: str | Path) -> None:
    subprocess.run(
        ["npx", *map(str, args)],
        check=True,
        shell=sys.platform == "win32",
    )
