import contextlib
import pathlib
import subprocess
import sys
import typing as t
from pathlib import Path

import imy.docstrings
import introspection.types
import introspection.typing
import pandas
import polars

import rio.docs

ALIASES: dict[object, str] = {
    obj: f"rio.{doc.name}"
    for obj, doc in rio.docs.get_toplevel_documented_objects().items()
}
ALIASES[pandas.DataFrame] = "pandas.DataFrame"
ALIASES[polars.DataFrame] = "polars.DataFrame"


def main() -> None:
    stub_file_path = Path(rio.__file__).absolute().parent / "__init__temp.pyi"

    with stub_file_path.open("w", encoding="utf8") as stub_file:
        writer = StubWriter(stub_file)

        for docs in rio.docs.get_toplevel_documented_objects().values():
            writer.write(docs)

    # Run the file through a linter to ensure its correctness
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(stub_file_path)],
        check=True,
    )

    subprocess.run(
        [sys.executable, "-m", "ruff", "format", str(stub_file_path)],
        check=True,
    )


class StubWriter:
    def __init__(self, file: t.TextIO):
        self._file = file
        self._indent = 0

        self._write("""
import datetime
import os
import pathlib
import typing

import numpy
import pandas
import polars
import PIL.Image
import yarl

import rio


""")

    @contextlib.contextmanager
    def _indented(self):
        self._indent += 1
        yield
        self._indent -= 1

    def _write_line(self, line: str) -> None:
        self._write_indented(line)
        self._write("\n")

    def _write_indented(self, text: str) -> None:
        self._write("    " * self._indent)
        self._write(text)

    def _write(self, text: str) -> None:
        self._file.write(text)

    def write(
        self, docs: imy.docstrings.FunctionDocs | imy.docstrings.ClassDocs
    ) -> None:
        if docs.object is rio.URL:
            self._write_line(f"{docs.name} = yarl.URL")
            return

        if isinstance(docs, imy.docstrings.FunctionDocs):
            self._write_function(docs)
        else:
            self._write_class(docs)

    def _write_function(self, docs: imy.docstrings.FunctionDocs) -> None:
        if docs.class_method:
            self._write_line("@classmethod")
        elif docs.static_method:
            self._write_line("@staticmethod")

        self._write_function_signature(docs)

        with self._indented():
            if docs.summary or docs.details:
                self._write_docstring(docs)
            else:
                self._write_line("...")

        self._write("\n")

    def _write_function_signature(
        self, docs: imy.docstrings.FunctionDocs
    ) -> None:
        if not docs.parameters:
            self._write_line(f"def {docs.name}():")
            return

        self._write_line(f"def {docs.name}(")

        with self._indented():
            already_kw_only = False

            for parameter in docs.parameters.values():
                if parameter.collect_positional:
                    name = "*" + parameter.name
                    already_kw_only = True
                elif parameter.collect_keyword:
                    name = "**" + parameter.name
                    already_kw_only = True
                elif parameter.kw_only and not already_kw_only:
                    self._write_line("*,")
                    name = parameter.name
                    already_kw_only = True
                else:
                    name = parameter.name

                self._write_annotated_name(
                    name, parameter.type, parameter.default, end=",\n"
                )

        self._write_line("):")

    def _write_annotated_name(
        self,
        name: str,
        type_: introspection.types.TypeAnnotation | imy.docstrings.Unset,
        default_value: object | imy.docstrings.Unset = imy.docstrings.UNSET,
        *,
        end: str = "\n",
        force_annotation: bool = False,
    ) -> None:
        self._write_indented(name)

        if isinstance(type_, imy.docstrings.Unset):
            if force_annotation:
                self._write(": typing.Any")
        else:
            self._write(": ")
            self._write(
                introspection.typing.annotation_to_string(
                    type_, implicit_typing=False, aliases=ALIASES
                )
            )

        if not isinstance(default_value, imy.docstrings.Unset):
            self._write(f" = {repr_value(default_value)}")

        self._write(end)

    def _write_docstring(
        self, docs: imy.docstrings.FunctionDocs | imy.docstrings.ClassDocs
    ) -> None:
        docstring = "\n\n".join(filter(None, [docs.summary, docs.details]))

        if not docstring:
            return

        self._write_line(repr(docstring))
        self._write("\n")

    def _write_class(self, docs: imy.docstrings.ClassDocs) -> None:
        if docs.object is not rio.Component:
            self._write_line("@typing.final")

        self._write_indented(f"class {docs.name}")
        self._write_base_classes(docs)
        self._write(":\n")

        with self._indented():
            self._write_docstring(docs)

            for attr in docs.attributes.values():
                self._write_annotated_name(attr.name, attr.type)

            if docs.attributes:
                self._write("\n")

            for method in docs.functions.values():
                self._write_function(method)

        self._write("\n")

    def _write_base_classes(self, docs: imy.docstrings.ClassDocs) -> None:
        public_base_classes = [
            rio.docs.get_all_documented_objects()[cls]
            for cls in docs.object.__bases__
            if cls in rio.docs.get_all_documented_objects()
        ]

        if not public_base_classes:
            return

        self._write("(")
        self._write(", ".join(docs.name for docs in public_base_classes))
        self._write(")")


def repr_value(value: object) -> str:
    if isinstance(value, (pathlib.WindowsPath, pathlib.PosixPath)):
        return f"pathlib.Path({value})"

    value_repr = repr(value)

    # Some objects, like functions, don't have a proper repr. Replace
    # those values with "...".
    if value_repr.startswith("<"):
        return "..."

    # Replace occurrences of "WindowsPath" and "PosixPath". (This is done as a
    # string operation because path objects can appear in nested data
    # structures. We don't want to recurse into every container just to call
    # `isinstance(..., (WindowsPath, PosixPath))` on every object.)
    value_repr = value_repr.replace("WindowsPath(", "pathlib.Path(")
    value_repr = value_repr.replace("PosixPath(", "pathlib.Path(")

    # Remove type annotations for sentinel default values
    value_repr = value_repr.replace(" | rio.text_style.UnsetType", "")

    return value_repr


if __name__ == "__main__":
    main()
