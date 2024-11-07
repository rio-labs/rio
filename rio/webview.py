__all__ = ["webview"]


# There is an issue with `rye test`. rye passes a `--rootdir` argument to
# pytest, and webview parses command line arguments when it is imported. It
# crashes parsing the `--rootdir` argument, so we'll temporarily remove the
# command line arguments while importing webview.
import sys

argv = sys.argv
sys.argv = argv[:1]

try:
    import webview
except ImportError:
    pass
finally:
    sys.argv = argv
