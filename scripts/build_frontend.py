import subprocess
from pathlib import Path

import rio.utils

PROJECT_ROOT_DIR = rio.utils.PROJECT_ROOT_DIR.relative_to(Path.cwd())
INPUT_DIR = PROJECT_ROOT_DIR / "frontend"
OUTPUT_DIR = Path("..") / "rio" / "frontend files"


def build(*extra_args: str):
    npx(
        "vite",
        "build",
        INPUT_DIR,
        "--outDir",
        OUTPUT_DIR,
        "--config",
        PROJECT_ROOT_DIR / "vite.config.js",
        "--base",
        "/rio/frontend",
        "--emptyOutDir",
        *extra_args,
    )


def dev_build():
    build("--mode", "development", "--minify", "false")


def npx(*args: str | Path) -> str:
    process = subprocess.run(
        ["npx", *map(str, args)],
        check=True,
        shell=True,
        capture_output=True,
        text=True,
    )
    return process.stdout
