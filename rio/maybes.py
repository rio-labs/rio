"""
This module exposes functionality which may or may not exist, depending on which
modules are available on the system.

Some values are not initialized at all, if the required module isn't in
`sys.modules`. This avoids long startup times if modules are available but not
used.
"""

from __future__ import annotations

import sys
import typing as t

import introspection
import narwhals.typing as nwt

if t.TYPE_CHECKING:
    import matplotlib.axes  # type: ignore
    import matplotlib.figure  # type: ignore
    import numpy  # type: ignore
    import plotly.graph_objects  # type: ignore

_IS_INITIALIZED = False

T = t.TypeVar("T")


FLOAT_TYPES = ()
INT_TYPES = ()
BOOL_TYPES = ()
STR_TYPES = ()

NUMPY_ARRAY_TYPES: tuple[type[numpy.ndarray], ...] = ()

DATAFRAME_TYPES: tuple[type[nwt.IntoDataFrame], ...] = ()

PLOTLY_GRAPH_TYPES: tuple[type[plotly.graph_objects.Figure], ...] = ()
MATPLOTLIB_GRAPH_TYPES: tuple[type, ...] = ()
MATPLOTLIB_AXES_TYPES: tuple[type[matplotlib.axes.Axes], ...] = ()

# This is a mapping of "weird" types to the "canonical" type, like `{np.int8:
# int}`
TYPE_NORMALIZERS: dict[type[T], t.Callable[[T], T]] = {}  # type: ignore


def initialize(force: bool = False) -> None:
    """
    If called for the first time, initialize all constants in the module. This
    is not automatically done on module load, to make sure any needed modules
    have already been imported - some functionality is not initialized if those
    other modules aren't used.

    If `force` is `True` everything is initialized even if it was already
    initialized previously.
    """
    global _IS_INITIALIZED
    global FLOAT_TYPES, INT_TYPES, BOOL_TYPES, STR_TYPES
    global NUMPY_ARRAY_TYPES
    global DATAFRAME_TYPES
    global PLOTLY_GRAPH_TYPES, MATPLOTLIB_GRAPH_TYPES, MATPLOTLIB_AXES_TYPES

    # Already initialized?
    if _IS_INITIALIZED and not force:
        return

    _IS_INITIALIZED = True

    FLOAT_TYPES = (float, int)
    INT_TYPES = (int,)
    BOOL_TYPES = (bool,)
    STR_TYPES = (str,)

    DATAFRAME_TYPES = ()

    # Is numpy available and loaded?
    if "numpy" in sys.modules:
        import numpy  # type: ignore

        NUMPY_ARRAY_TYPES = (numpy.ndarray,)

        numpy_floats = tuple(introspection.iter_subclasses(numpy.floating))
        numpy_ints = tuple(introspection.iter_subclasses(numpy.integer))
        numpy_bools = tuple(introspection.iter_subclasses(numpy.bool_))
        numpy_strings = tuple(introspection.iter_subclasses(numpy.str_))

        FLOAT_TYPES = (*FLOAT_TYPES, *numpy_floats, *numpy_ints)
        INT_TYPES += numpy_ints
        BOOL_TYPES += numpy_bools
        STR_TYPES += numpy_strings

    if "pandas" in sys.modules:
        import pandas  # type: ignore

        DATAFRAME_TYPES += (pandas.DataFrame,)

    if "polars" in sys.modules:
        import polars  # type: ignore

        DATAFRAME_TYPES += (polars.DataFrame,)

    if "plotly" in sys.modules:
        import plotly.graph_objects  # type: ignore

        PLOTLY_GRAPH_TYPES = (plotly.graph_objects.Figure,)

    if "matplotlib" in sys.modules:
        import matplotlib.axes  # type: ignore
        import matplotlib.figure  # type: ignore

        MATPLOTLIB_AXES_TYPES = (matplotlib.axes.Axes,)
        MATPLOTLIB_GRAPH_TYPES = (
            matplotlib.figure.Figure,
        ) + MATPLOTLIB_AXES_TYPES

    # Populate our mapping of type normalizers
    for canonical_type, weird_types in (
        (str, STR_TYPES),
        (bool, BOOL_TYPES),
        (int, INT_TYPES),
        (float, FLOAT_TYPES),
    ):
        for weird_type in weird_types:
            TYPE_NORMALIZERS[weird_type] = canonical_type  # type: ignore
