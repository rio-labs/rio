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
from typing import Callable, IO, Optional

import revel
from dataclasses import dataclass

@dataclass
class FormatStyle:
    bold: str
    nobold: str
    dim: str
    nodim: str
    yellow: str
    noyellow: str
    red: str
    nored: str
    escape: Callable[[str], str]


def _handle_syntax_error(err: SyntaxError) -> traceback.FrameSummary:
    """
    Create a FrameSummary for a SyntaxError, handling differences between Python versions.
    """
    if sys.version_info < (3, 11):
        return traceback.FrameSummary(
            filename=err.filename,
            lineno=err.lineno,
            name="<module>",
            line=err.text,
            locals=None,
        )
    else:
        return traceback.FrameSummary(
            filename=err.filename,
            lineno=err.lineno,
            end_lineno=err.end_lineno,
            colno=err.offset,
            end_colno=err.end_offset,
            name="<module>",
            line=err.text,
            locals=None,
        )
    
def _format_single_exception_raw(
    out: IO[str],
    err: BaseException,
    *,
    include_header: bool,
    style: FormatStyle,
    relpath: Optional[Path],
    frame_filter: Callable[[traceback.FrameSummary], bool],
) -> None:
    """
    Format a single exception and write it to the output stream.
    """
    tb_list = traceback.extract_tb(err.__traceback__)

    if isinstance(err, SyntaxError):
        frame = _handle_syntax_error(err)
        tb_list.append(frame)

    if include_header:
        out.write(f"{style.dim}Traceback (most recent call last):{style.nodim}\n")

    for frame in tb_list:
        if not frame_filter(frame):
            continue

        frame_path = Path(frame.filename)
        if relpath and frame_path.is_absolute():
            try:
                frame_path = frame_path.relative_to(relpath)
            except ValueError:
                pass

        out.write(
            f"  {style.dim}File{style.nodim} {style.yellow}{style.escape(str(frame_path))}{style.noyellow}"
            f"{style.dim}, {style.nodim}line {frame.lineno}{style.noyellow}{style.dim}, in {style.escape(frame.name)}{style.nodim}\n"
        )

        source_line = linecache.getline(frame.filename, frame.lineno).strip()
        if source_line:
            if (
                frame is tb_list[-1]
                and getattr(frame, "colno", None) is not None
                and getattr(frame, "end_colno", None) is not None
            ):
                before = style.escape(source_line[: frame.colno])
                error = style.escape(source_line[frame.colno : frame.end_colno])
                after = style.escape(source_line[frame.end_colno :])
                formatted_line = f"{before}{style.red}{error}{style.nored}{after}"
            else:
                formatted_line = style.escape(source_line)
            out.write(f"    {formatted_line}\n")

    out.write("\n")
    out.write(f"{style.bold}{style.red}{type(err).__name__}{style.nored}{style.nobold}")

    error_message = str(err)
    if error_message:
        out.write(f"{style.bold}: {style.escape(error_message)}{style.nobold}")


def format_exception_raw(
    err: BaseException,
    *,
    style: FormatStyle,
    relpath: Optional[Path] = None,
    frame_filter: Optional[Callable[[traceback.FrameSummary], bool]] = None,
) -> str:
    """
    Format an exception into a pretty string with the given style.
    """
    frame_filter = frame_filter or (lambda _: True)

    def format_inner(current_err: BaseException) -> None:
        nonlocal include_header
        if current_err.__cause__ is not None:
            format_inner(current_err.__cause__)
            out.write("\n\n")
            out.write("The above exception was the direct cause of the following:\n\n")
            include_header = False
        elif current_err.__context__ is not None:
            format_inner(current_err.__context__)
            out.write("\n\n")
            out.write("During handling of the above exception, another exception occurred:\n\n")
            include_header = False
        else:
            include_header = True

        _format_single_exception_raw(
            out,
            current_err,
            include_header=include_header,
            style=style,
            relpath=relpath,
            frame_filter=frame_filter,
        )

    include_header = True
    out = io.StringIO()
    format_inner(err)
    return out.getvalue()

def format_exception_revel(
    err: BaseException,
    *,
    relpath: Optional[Path] = None,
    frame_filter: Optional[Callable[[traceback.FrameSummary], bool]] = None,
) -> str:
    """
    Format an exception using Revel's styling.
    """
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
    return format_exception_raw(
        err,
        style=style,
        relpath=relpath,
        frame_filter=frame_filter,
    )


def format_exception_html(
    err: BaseException,
    *,
    relpath: Optional[Path] = None,
    frame_filter: Optional[Callable[[traceback.FrameSummary], bool]] = None,
) -> str:
    """
    Format an exception into HTML with appropriate styling.
    """
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
    result = format_exception_raw(
        err,
        style=style,
        relpath=relpath,
        frame_filter=frame_filter,
    )
    return result.replace("\n", "<br>")