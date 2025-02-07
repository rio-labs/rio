"""
Pretty-strings a traceback. The result looks very similar to Python's default,
but is colored and just tweaked in general.
"""

import dataclasses
import html
import io
import itertools
import linecache
import os
import sys
import traceback
import typing as t
from pathlib import Path

import path_imports
import revel

import rio

__all__ = [
    "format_exception_revel",
    "format_exception_html",
    "FormatStyle",
    "print_exception",
]


def print_exception(
    error: BaseException, *, relpath: Path | None = None
) -> None:
    text = format_exception_revel(error, relpath=relpath)
    revel.print(text)


@dataclasses.dataclass
class FormatStyle:
    bold: str
    nobold: str
    dim: str
    nodim: str
    yellow: str
    noyellow: str
    red: str
    nored: str
    escape: t.Callable[[str], str]


def _handle_syntax_error(err: SyntaxError) -> traceback.FrameSummary:
    """
    Syntax errors are very special snowflakes and need separate treatment. This
    creates a FrameSummary for a SyntaxError, handling differences between
    Python versions.
    """
    filename = err.filename or "<unknown>"

    # TODO: Is there a better way to do this? Since Python obviously isn't
    # keeping the arguments consistent, this could potentially break every
    # single Python version.
    if sys.version_info < (3, 11):
        return traceback.FrameSummary(
            filename=filename,
            lineno=err.lineno,
            name="<module>",
            line=err.text,
            locals=None,
        )
    else:
        return traceback.FrameSummary(
            filename=filename,
            lineno=err.lineno,
            end_lineno=err.end_lineno,
            colno=None if err.offset is None else err.offset - 1,
            end_colno=None if err.end_offset is None else err.end_offset - 1,
            name="<module>",
            line=err.text,
            locals=None,
        )


def remove_rio_internals_from_traceback(
    tb: list[traceback.FrameSummary],
) -> t.Sequence[traceback.FrameSummary]:
    # Skip frames which are internal to rio (or libraries used by rio) until we
    # hit the first non-rio frame. Then include everything.
    rio_root = rio.__file__
    assert rio_root.endswith(os.sep + "__init__.py")
    rio_root = rio_root.removesuffix(os.sep + "__init__.py")

    def predicate(frame: traceback.FrameSummary) -> bool:
        return (
            frame.filename.startswith((rio_root, "<frozen importlib"))
            or frame.filename == path_imports.__file__
        )

    return list(itertools.dropwhile(predicate, tb))


def _format_single_exception_raw(
    out: t.IO[str],
    err: BaseException,
    *,
    include_header: bool,
    style: FormatStyle,
    relpath: Path | None,
) -> None:
    """
    Format a single exception and write it to the output stream.
    """
    tb_list = traceback.extract_tb(err.__traceback__)

    # Syntax errors need special handling. Convert them to something that
    # behaves more like a regular one.
    if isinstance(err, SyntaxError):
        tb_list.append(_handle_syntax_error(err))

    tb_list = remove_rio_internals_from_traceback(tb_list)

    # TODO: Add special handling for recursion errors. Instead of printing the
    # same frame 1000 times, print a message like "Last 5 frames repeated 200
    # times".

    # Lead-in
    if include_header:
        out.write(
            f"{style.dim}Traceback (most recent call last):{style.nodim}\n"
        )

    # Walk all frames and format them
    for frame in tb_list:
        assert frame.lineno is not None

        # Make paths relative to `relpath` if they're contained within
        frame_path = Path(frame.filename)
        if relpath and frame_path.is_absolute():
            try:
                frame_path = frame_path.relative_to(relpath)
            except ValueError:
                pass

        # File location
        out.write(
            f"  {style.dim}File{style.nodim} {style.yellow}{style.escape(str(frame_path))}{style.noyellow}"
            f"{style.dim}, {style.nodim}line {frame.lineno}{style.noyellow}{style.dim}, in {style.escape(frame.name)}{style.nodim}\n"
        )

        # Display the source code from this line
        #
        # Insanely, the line in the frame has been stripped. Refetch it.
        source_line = linecache.getline(frame.filename, frame.lineno)
        if source_line:
            # If this is the last line, highlight the error
            if (
                frame is tb_list[-1]
                and hasattr(frame, "colno")
                and hasattr(frame, "end_colno")
                and frame.colno is not None  # type: ignore
                and frame.end_colno is not None  # type: ignore
            ):
                start_col = frame.colno  # type: ignore

                if (
                    hasattr(frame, "end_lineno")
                    and frame.end_lineno is not None  # type: ignore
                    and frame.end_lineno > frame.lineno  # type: ignore
                ):
                    end_col = len(source_line) - 1  # -1 to exclude the \n
                else:
                    end_col = frame.end_colno  # type: ignore

                before = style.escape(source_line[:start_col].lstrip())
                error = style.escape(source_line[start_col:end_col])
                after = style.escape(source_line[end_col:].rstrip())
                formatted_line = (
                    f"{before}{style.red}{error}{style.nored}{after}"
                )
            else:
                formatted_line = style.escape(source_line.strip())

            # Write the line
            out.write(f"    {formatted_line}\n")

    # Exception type and message
    out.write("\n")
    out.write(
        f"{style.bold}{style.red}{type(err).__name__}{style.nored}{style.nobold}"
    )

    error_message = str(err)

    if error_message:
        out.write(f"{style.bold}: {style.escape(error_message)}{style.nobold}")


def format_exception_raw(
    err: BaseException,
    *,
    style: FormatStyle,
    relpath: Path | None = None,
) -> str:
    """
    Format an exception into a pretty string with the given style.
    """

    def format_inner(current_err: BaseException) -> None:
        # Chain to the cause or context if there is one
        if current_err.__cause__ is not None:
            format_inner(current_err.__cause__)
            out.write("\n\n")
            out.write(
                "The above exception was the direct cause of the following:\n\n"
            )
            include_header = False
        elif current_err.__context__ is not None:
            format_inner(current_err.__context__)
            out.write("\n\n")
            out.write(
                "During handling of the above exception, another exception occurred:\n\n"
            )
            include_header = False
        else:
            include_header = True

        # Format the exception
        _format_single_exception_raw(
            out,
            current_err,
            include_header=include_header,
            style=style,
            relpath=relpath,
        )

    # Format
    out = io.StringIO()
    format_inner(err)
    return out.getvalue()


def format_exception_revel(
    err: BaseException,
    *,
    relpath: Path | None = None,
) -> str:
    """
    Format an exception using revel's styling.
    """

    # Prepare the style
    style = FormatStyle(
        bold="[bold]",
        nobold="[/]",
        dim="[dim]",
        nodim="[/]",
        yellow="[yellow]",
        noyellow="[/]",
        red="[red]",
        nored="[/]",
        escape=revel.escape,
    )

    # Format the exception
    return format_exception_raw(
        err,
        style=style,
        relpath=relpath,
    )


def format_exception_html(
    err: BaseException,
    *,
    relpath: Path | None = None,
) -> str:
    """
    Format an exception into HTML with appropriate styling.
    """

    # Prepare the style
    style = FormatStyle(
        bold='<span class="rio-traceback-bold">',
        nobold="</span>",
        dim='<span class="rio-traceback-dim">',
        nodim="</span>",
        yellow='<span class="rio-traceback-yellow">',
        noyellow="</span>",
        red='<span class="rio-traceback-red">',
        nored="</span>",
        escape=html.escape,
    )

    # Format the exception
    result = format_exception_raw(
        err,
        style=style,
        relpath=relpath,
    )

    # HTML-ify newlines
    return result.replace("\n", "<br>")
