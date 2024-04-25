"""
Pretty-strings a traceback. The result looks very similar to Python's default,
but is colored and just tweaked in general.
"""

import html
import io
import linecache
import sys
import traceback
from pathlib import Path
from typing import *  # type: ignore

import revel


def _format_single_exception_raw(
    out: IO[str],
    err: BaseException,
    *,
    include_header: bool,
    escape: Callable[[str], str],
    bold: str,
    nobold: str,
    dim: str,
    nodim: str,
    yellow: str,
    noyellow: str,
    red: str,
    nored: str,
    relpath: Path | None = None,
    frame_filter: Callable[[traceback.FrameSummary], bool],
) -> None:
    # Get the traceback as a list of frames
    tb_list = traceback.extract_tb(err.__traceback__)

    # Syntax errors are very special snowflakes and need separate treatment.
    #
    # The exact arguments depend on the python version.
    #
    # TODO: Is there a better way to do this? Since Python obviously isn't
    # keeping the arguments consistent, this could potentially break every
    # single Python version.
    if isinstance(err, SyntaxError):
        if sys.version_info < (3, 11):
            frame = traceback.FrameSummary(
                filename=err.filename,  # type: ignore
                lineno=err.lineno,
                name="<module>",
                line=err.text,
                locals=None,
            )
        else:
            frame = traceback.FrameSummary(
                filename=err.filename,  # type: ignore
                lineno=err.lineno,
                end_lineno=err.end_lineno,
                colno=err.offset,
                end_colno=err.end_offset,
                name="<module>",
                line=err.text,
                locals=None,
            )

        tb_list.append(frame)

    # Lead-in
    if include_header:
        out.write(f"{dim}Traceback (most recent call last):{nodim}\n")

    # Iterate through frames
    for frame in tb_list:
        # Keep this frame?
        if not frame_filter(frame):
            continue

        # Make paths relative to the relpath if they're inside it
        frame_path = Path(frame.filename)

        if relpath is not None and frame_path.is_absolute():
            try:
                frame_path = frame_path.relative_to(relpath)
            except ValueError:
                pass

        # Format the file location
        out.write(
            f"  {dim}File{nodim} {yellow}{escape(str(frame_path))}{noyellow}{dim}, {nodim}{yellow}line {frame.lineno}{noyellow}{dim}, in {escape(frame.name)}{nodim}\n"
        )

        # Display the source code from that line
        #
        # Insanely, the line in the frame has been stripped. Fetch it again.
        assert frame.lineno is not None  # Doesn't seem to happen, ever
        line = linecache.getline(frame.filename, frame.lineno)

        if line.strip():
            # If this is the last line, highlight the error
            if (
                frame is tb_list[-1]
                and hasattr(frame, "colno")
                and hasattr(frame, "end_colno")
            ):
                assert frame.colno is not None  # type: ignore
                assert frame.end_colno is not None  # type: ignore

                before = escape(line[: frame.colno])  # type: ignore
                error = escape(line[frame.colno : frame.end_colno])  # type: ignore
                after = escape(line[frame.end_colno :])  # type: ignore
                line = f"{before}{red}{error}{nored}{after}"
            else:
                line = escape(line)

            # NOW strip it
            line = line.strip()
            out.write(f"    {line}\n")

    # Actual error message
    out.write("\n")
    out.write(f"{bold}{red}{type(err).__name__}{nored}{nobold}")

    error_message = str(err)
    if error_message:
        out.write(f"{bold}: {escape(str(err))}{nobold}")


def format_exception_raw(
    err: BaseException,
    *,
    escape: Callable[[str], str],
    bold: str,
    nobold: str,
    dim: str,
    nodim: str,
    yellow: str,
    noyellow: str,
    red: str,
    nored: str,
    relpath: Path | None = None,
    frame_filter: Callable[[traceback.FrameSummary], bool] = lambda _: True,
) -> str:
    def format_inner(err: BaseException) -> None:
        # Chain to the cause or context if there is one
        if err.__cause__ is not None:
            format_inner(err.__cause__)
            out.write("\n\n")
            out.write(
                f"The above exception was the direct cause of the following:\n\n"
            )
            include_header = False

        elif err.__context__ is not None:
            format_inner(err.__context__)
            out.write("\n\n")
            out.write(
                f"During handling of the above exception, another exception occurred:\n\n"
            )
            include_header = False
        else:
            include_header = True

        # Format this exception
        _format_single_exception_raw(
            out,
            err,
            include_header=include_header,
            escape=escape,
            bold=bold,
            nobold=nobold,
            dim=dim,
            nodim=nodim,
            yellow=yellow,
            noyellow=noyellow,
            red=red,
            nored=nored,
            relpath=relpath,
            frame_filter=frame_filter,
        )

    # Start the recursion
    out = io.StringIO()
    format_inner(err)

    # Return the result
    return out.getvalue()


def format_exception_revel(
    err: BaseException,
    *,
    relpath: Path | None = None,
    frame_filter: Callable[[traceback.FrameSummary], bool] = lambda _: True,
) -> str:
    return format_exception_raw(
        err,
        bold="[bold]",
        nobold="[/]",
        dim="[dim]",
        nodim="[/]",
        yellow="[yellow]",
        noyellow="[/]",
        red="[red]",
        nored="[/]",
        escape=revel.escape,
        relpath=relpath,
        frame_filter=frame_filter,
    )


def format_exception_html(
    err: BaseException,
    *,
    relpath: Path | None = None,
    frame_filter: Callable[[traceback.FrameSummary], bool] = lambda _: True,
) -> str:
    result = format_exception_raw(
        err,
        bold='<span class="rio-traceback-bold">',
        nobold="</span>",
        dim='<span class="rio-traceback-dim">',
        nodim="</span>",
        yellow='<span class="rio-traceback-yellow">',
        noyellow="</span>",
        red='<span class="rio-traceback-red">',
        nored="</span>",
        escape=html.escape,
        relpath=relpath,
        frame_filter=frame_filter,
    )

    return result.replace("\n", "<br>")
