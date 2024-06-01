import subprocess
import sys
from pathlib import Path

import rio.utils

PROJECT_ROOT_DIR = rio.utils.PROJECT_ROOT_DIR
INPUT_DIR = PROJECT_ROOT_DIR / "frontend"
OUTPUT_DIR = PROJECT_ROOT_DIR / "rio" / "frontend files"
ASSETS_DIR = OUTPUT_DIR / "assets"


def build(*extra_args: str):
    npx(
        "vite",
        "build",
        INPUT_DIR,
        "--outDir",
        OUTPUT_DIR,
        "--config",
        PROJECT_ROOT_DIR / "vite.config.mjs",
        "--base",
        "/rio/frontend",
        "--emptyOutDir",
        *extra_args,
    )


def dev_build():
    build("--mode", "development", "--minify", "false")


def npx(*args: str | Path) -> None:
    subprocess.run(
        ["npx", *map(str, args)],
        check=True,
        shell=sys.platform == "win32",
    )
