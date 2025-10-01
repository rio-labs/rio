"""
This script updates all dependencies and dev-dependencies in the package.json to
the newest version.
"""

from ._utils import npm, npx

npx("npm-check-updates", "-u")
npm("install")
