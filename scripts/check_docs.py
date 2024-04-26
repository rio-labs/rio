"""
Helper script for running checks on documentation, such as looking for missing
docstrings.
"""

import sys
from pathlib import Path
from typing import *  # type: ignore

import imy.docstrings

# Some rio modules optionally depend on libraries and evaling their type
# annotations can fail if they're not installed. Import them explicitly here to produce more obvious error messages
from revel import *  # type: ignore

# Make sure `rio.docs` can be imported
sys.path.append(str(Path(__file__).absolute().parent.parent))

import rio_website.article_models

import rio.docs


def check_function(
    docs: imy.docstrings.FunctionDocs,
    owning_cls: type | None,
) -> None:
    qualname = (
        f"{owning_cls.__name__}.{docs.name}"
        if owning_cls is not None
        else docs.name
    )

    # __init__ methods for components need no documentation, since the
    # class' documentation already fills that role
    if (
        docs.name == "__init__"
        and owning_cls is not None
        and issubclass(owning_cls, rio.Component)
    ):  # type: ignore
        return

    # Run checks
    if docs.name != "__init__":
        if docs.summary is None:
            warning(
                f"Docstring for `{qualname}` is missing a short description"
            )

        if docs.details is None:
            warning(f"Docstring for `{qualname}` is missing a long description")

        if docs.return_type is imy.docstrings.Unset:
            warning(f"`{qualname}` is missing a return type hint")

    # Chain to parameters
    for param in docs.parameters:
        if param.name == "self":
            continue

        if param.type is None:
            warning(
                f"`{qualname}` is missing a type hint for parameter `{param.name}`"
            )

        if param.description is None:
            warning(
                f"Docstring for `{qualname}` is missing a description for parameter `{param.name}`"
            )


def check_class(cls: type, docs: imy.docstrings.ClassDocs) -> None:
    # Run checks
    if docs.summary is None:
        warning(f"Docstring for `{docs.name}` is missing a short description")

    if docs.details is None:
        warning(f"Docstring for `{docs.name}` is missing a long description")

    for attr in docs.attributes:
        if attr.description is None:
            warning(
                f"Docstring for `{docs.name}.{attr.name}` is missing a description"
            )

    for func_docs in docs.functions:
        check_function(func_docs, cls)


def main() -> None:
    print_chapter("Saving you hours of debugging")
    print(
        "Note: If you get an error about an undefined value (usually a "
        "type), you're most likely missing a `from typing import *` in one "
        "of rio's files."
    )
    print()
    print(
        "An easy way to find out is to run this script in a debugger and "
        "have it stop on exceptions. Go up one scope in the stack and "
        "display the value of `globalns`."
    )

    # Find all items that should be documented
    print_chapter("Looking for objects in the Rio module")
    public_objects = {
        obj: docs
        for obj, docs in rio.docs.find_documented_objects(postprocess=True)
        if docs.metadata.public
    }

    print(f"Found {len(public_objects)} items")

    # Make sure they're all properly documented
    print_chapter("Making you depressed")
    for item, docs in public_objects.items():
        # Classes / Components
        if isinstance(docs, imy.docstrings.ClassDocs):
            item = cast(type, item)
            check_class(item, docs)
        else:
            check_function(docs, None)

    # Make sure all items are displayed Rio's documentation
    visited_objects: set[object] = set()

    for _, _, _, objects in rio_website.structure.API_DOCS_SECTIONS:
        visited_objects.update(objects)

    unvisited_objects = public_objects.keys() - visited_objects
    for obj in unvisited_objects:
        warning(f"Item `{obj.__name__}` is not displayed in the documentation")


if __name__ == "__main__":
    main()
