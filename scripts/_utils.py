import subprocess
import sys

__all__ = ["npm", "npx"]


def _npm_command(command: str, *args: str):
    subprocess.run(
        [command, *args],
        check=True,
        shell=sys.platform == "win32",
    )


def npm(*args: str):
    _npm_command("npm", *args)


def npx(*args: str):
    _npm_command("npx", *args)
