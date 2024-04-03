"""
Helper script for running checks on documentation, such as looking for missing
docstrings.
"""

import inspect
import sys
from pathlib import Path
from typing import *  # type: ignore

# Some rio modules optionally depend on libraries and evaling their type
# annotations can fail if they're not installed. Import them explicitly here to produce more obvious error messages
import matplotlib
import pandas
import plotly
import polars
from revel import *  # type: ignore

# Make sure `rio_docs` can be imported
sys.path.append(str(Path(__file__).absolute().parent.parent))

import rio
import rio_docs
import website


def check_function(
    docs: rio_docs.FunctionDocs,
    owning_cls: type | None,
) -> None:
    qualname = (
        f"{owning_cls.__name__}.{docs.name}" if owning_cls is not None else docs.name
    )

    # __init__ methods for components need no documentation, since the
    # class' documentation already fills that role
    if docs.name == "__init__" and owning_cls is not None and issubclass(owning_cls, rio.Component):  # type: ignore
        return

    # Run checks
    if docs.summary is None and docs.name != "__init__":
        warning(f"Docstring for `{qualname}` is missing a short description")

    if docs.details is None and docs.name != "__init__":
        warning(f"Docstring for `{qualname}` is missing a long description")

    if docs.return_type is None:
        warning(f"`{qualname}` is missing a return type hint")

    # Chain to parameters
    for param in docs.parameters:
        if param.name == "self":
            continue

        if param.type is None:
            warning(f"`{qualname}` is missing a type hint for parameter `{param.name}`")

        if param.description is None:
            warning(
                f"Docstring for `{qualname}` is missing a description for parameter `{param.name}`"
            )


def check_class(cls: type, docs: rio_docs.ClassDocs) -> None:
    # Run checks
    if docs.summary is None:
        warning(f"Docstring for `{docs.name}` is missing a short description")

    if docs.details is None:
        warning(f"Docstring for `{docs.name}` is missing a long description")

    for attr in docs.attributes:
        if attr.description is None:
            warning(f"Docstring for `{docs.name}.{attr.name}` is missing a description")

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
    print_chapter("Looking for items needing documentation")
    target_items: list[type | Callable[..., Any]] = list(
        rio_docs.custom.find_items_needing_documentation()
    )

    print(f"Found {len(target_items)} items")

    # Make sure they're all properly documented
    print_chapter("Making you depressed")
    for item in target_items:
        # Classes / Components
        if inspect.isclass(item):
            # Fetch the docs
            docs = rio_docs.ClassDocs.parse(item)

            # Post-process them as needed
            if isinstance(item, rio.Component):
                rio_docs.custom.postprocess_component_docs(docs)
            else:
                rio_docs.custom.postprocess_class_docs(docs)

            check_class(item, docs)

        else:
            assert inspect.isfunction(item), item

            docs = rio_docs.FunctionDocs.parse(item)

            check_function(docs, None)

    # Make sure all items are displayed Rio's documentation
    visited_item_names: set[str] = set()

    for entry in website.structure.DOCUMENTATION_STRUCTURE_LINEAR:
        section_name, section_url, builder = entry

        if not isinstance(builder, website.article_models.ArticleBuilder):
            continue

        visited_item_names.add(builder.component_class.__name__)

    for item in target_items:
        if item.__name__ not in visited_item_names:
            warning(f"Item `{item.__name__}` is not displayed in the documentation")


if __name__ == "__main__":
    main()
