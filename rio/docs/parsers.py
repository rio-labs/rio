from __future__ import annotations

import collections
import dataclasses
import inspect
import textwrap
import typing
from dataclasses import is_dataclass
from typing import *  # type: ignore

import introspection.typing
import revel
from uniserde import Jsonable

from rio import inspection

from . import models


def split_docstring_into_sections(docstring: str) -> tuple[str, dict[str, str]]:
    """
    Splits the given docstring into sections separated by markdown headings. The
    result is the part of the string before the first heading, and a dictionary
    mapping the heading names to the text of the sections ("the summary").

    If the docstring starts with a heading it will not create a separate section
    and the text of that section will be considered part of the summary.
    """
    # Drop the title if it exists
    if docstring.startswith("#"):
        docstring = docstring.split("\n", 1)[1]

    # Split the docstring into sections
    sections: dict[str, list[str]] = {}
    details: list[str] = []
    current_section: list[str] = details

    # Process the individual lines
    for line in docstring.splitlines():
        if line.startswith("#"):
            section_name = line.strip()
            current_section = sections.setdefault(section_name, [])
        else:
            current_section.append(line)

    # Post-process the sections
    def postprocess(section: list[str]) -> str:
        return "\n".join(section).strip()

    return postprocess(details), {
        name: postprocess(section) for name, section in sections.items()
    }


def parse_key_value_section(section_string: str) -> dict[str, str]:
    """
    Some docstring sections are formatted as a list of key-value pairs, such as
    this:

    ```
    key: A description of the key.
    `key_in_code`: A description of the key in code.
    ```

    This function splits such a section into a dictionary of key-value pairs.
    """
    result_lines: dict[str, list[str]] = {}
    current_value: list[str] = []

    # Process the lines individually
    for raw_line in section_string.splitlines():
        # Strip the line and calculate the indentation
        strip_line = raw_line.lstrip()
        indent = len(raw_line) - len(strip_line)
        strip_line = strip_line.rstrip()

        # Continuation of the previous value
        if indent > 0 or not strip_line:
            current_value.append(strip_line)
            continue

        # New value
        parts = strip_line.split(":", 1)

        if len(parts) == 1:
            revel.warning(
                f'Expected a new mapping (key: value), but got "{strip_line}"'
            )
            current_value.append(strip_line)
            continue

        key, value = parts
        key = key.strip().strip("`").strip()
        value = value.strip()
        current_value = [value]
        result_lines[key] = current_value

    # Convert the section values from lists to strings
    result: dict[str, str] = {}

    for key, lines in result_lines.items():
        result[key] = " ".join(lines).strip()

    return result


def parse_details(details: str) -> tuple[str | None, str | None]:
    """
    Given the details part of a docstring, split it into summary and details.
    Either value may be Nonne if they are not present in the original string.
    """
    details = details.strip()

    # Split into summary & details
    lines = details.split("\n")

    short_lines: list[str] = []
    long_lines: list[str] = []
    cur_lines = short_lines

    for raw_line in lines:
        strip_line = raw_line.strip()

        cur_lines.append(raw_line)

        if not strip_line:
            cur_lines = long_lines

    # Join the lines
    short_description = "\n".join(short_lines).strip()
    long_description = "\n".join(long_lines).strip()

    if not short_description:
        short_description = None

    if not long_description:
        long_description = None

    # Done
    return short_description, long_description


def str_type_hint(typ: type) -> str:
    # Make sure the type annotation has been parsed
    assert not isinstance(typ, str), typ

    # Then pretty-string the type
    return introspection.typing.annotation_to_string(typ)


def parse_docstring_basic(
    docstring: str,
) -> tuple[str | None, str | None, dict[str, str]]:
    """
    Parses a docstring into

    - summary
    - details
    - sections
    """

    # Dedent & strip
    docstring = textwrap.dedent(docstring).strip()

    # Split the docstring into sections
    details, sections = split_docstring_into_sections(docstring)

    # Split into summary and details
    summary, details = parse_details(details)

    # Done
    return summary, details, sections


def parse_docstring(
    docstring: str,
    *,
    key_sections: Iterable[str],
) -> tuple[str | None, str | None, dict[str, dict[str, str]]]:
    """
    Parses a docstring into

    - summary
    - details
    - sections

    Any sections listed in `key_sections` will be parsed as key-value pairs and
    returned as sections. Any remaining sections will be re-joined into the
    details.

    Any sections listed in `key_sections` that are not present in the docstring
    will be imputed as empty.
    """
    # Parse the docstring
    summary, details, sections = parse_docstring_basic(docstring)

    if details is None:
        details = ""

    # Find and parse all key-value sections
    key_sections = set(key_sections)
    key_value_sections: dict[str, dict[str, str]] = {}

    for section_name, section_contents in sections.items():
        # Key section?
        normalized_section_name = section_name.lstrip("#").strip().lower()

        if normalized_section_name in key_sections:
            key_value_sections[normalized_section_name] = parse_key_value_section(
                section_contents
            )

        # Text section
        else:
            details += f"\n\n{section_name}\n\n{section_contents}"

    # Don't keep around an empty details section
    details = details.strip()

    if not details:
        details = None

    # Make sure all requested sections are present
    missing_sections = key_sections - key_value_sections.keys()

    for missing_section in missing_sections:
        key_value_sections[missing_section] = {}

    # Done
    return summary, details, key_value_sections


def parse_function(func: Callable[..., Any]) -> models.FunctionDocs:
    """
    Given a function, parse its signature an docstring into a `FunctionDocs`
    object.
    """

    def parse_annotation(annotation: object) -> str | None:
        if annotation is inspect.Parameter.empty:
            return None

        # Recursive types can cause issues. In particular, we have `Jsonable`,
        # which is a recursive type, and `JsonDoc`, which references `Jsonable`.
        # So if a module imports `JsonDoc` but doesn't import `Jsonable`, it's
        # impossible to evaluate the forward reference `"Jsonable"` in that
        # module.
        #
        # A similar problem exists due to dataclasses: Every `Component`
        # subclass receives a constructor based on the type annotations in
        # `Component`, but of course the relevant imports aren't there.
        #
        # As a workaround, we'll make the missing names available in every
        # module.
        extra_globals = collections.ChainMap(
            {"Jsonable": Jsonable},
            vars(typing),  # type: ignore
        )

        annotation = introspection.typing.resolve_forward_refs(
            annotation,  # type: ignore
            func.__module__,
            extra_globals=extra_globals,
            mode="ast",
            treat_name_errors_as_imports=True,
            strict=True,
        )

        return str_type_hint(annotation)  # type: ignore

    # Parse the parameters
    signature = inspect.signature(func)
    parameters: dict[str, models.FunctionParameter] = {}

    for param_name, param in signature.parameters.items():
        if param.default == inspect.Parameter.empty:
            param_default = None
        else:
            param_default = repr(param.default)

        parameters[param_name] = models.FunctionParameter(
            name=param_name,
            type=parse_annotation(param.annotation),
            default=param_default,
            kw_only=param.kind == inspect.Parameter.KEYWORD_ONLY,
            collect_positional=param.kind == inspect.Parameter.VAR_POSITIONAL,
            collect_keyword=param.kind == inspect.Parameter.VAR_KEYWORD,
            description=None,
        )

    # Parse the docstring
    docstring = inspect.getdoc(func)

    if docstring is None:
        summary = None
        details = None
        raises = []
    else:
        summary, details, sections = parse_docstring(
            docstring,
            key_sections=["args", "raises"],
        )

        raw_params = sections["args"]
        raw_raises = sections["raises"]

        # Add any information learned about parameters from the docstring
        for param_name, param_details in raw_params.items():
            try:
                result_param = parameters[param_name]
            except KeyError:
                revel.warning(
                    f"The docstring for function `{func.__name__}` mentions a parameter `{param_name}` that does not exist in the function signature."
                )
                continue

            result_param.description = param_details

        # Add information about raised exceptions
        raises = list(raw_raises.items())

    # Build the result
    return models.FunctionDocs(
        name=func.__name__,
        parameters=list(parameters.values()),
        return_type=parse_annotation(signature.return_annotation),
        synchronous=not inspect.iscoroutinefunction(func),
        summary=summary,
        details=details,
        raises=raises,
    )


def _parse_class_docstring_with_inheritance(
    cls: type,
    *,
    key_sections: Iterable[str],
) -> tuple[str | None, str | None, dict[str, dict[str, str]]]:
    """
    Parses the docstring of a class in the same format as `parse_docstring`, but
    accounts for inheritance: Key-Value sections of all classes are merged, in a
    way that preserves child docs over parent docs.
    """

    # Parse the docstring for this class
    raw_docs = inspect.getdoc(cls)
    key_sections = set(key_sections)
    parsed_docs = parse_docstring(
        "" if raw_docs is None else raw_docs,
        key_sections=key_sections,
    )

    # Get the docstrings for the base classes
    base_docs: list[tuple[str | None, str | None, dict[str, dict[str, str]]]] = []

    for base in cls.__bases__:
        base_docs.append(
            _parse_class_docstring_with_inheritance(
                base,
                key_sections=key_sections,
            )
        )

    # Merge the docstrings
    result_sections: dict[str, dict[str, str]] = {}
    all_in_order = base_docs + [parsed_docs]

    for docs in all_in_order:
        for section_name, section in docs[2].items():
            result_section = result_sections.setdefault(section_name, {})
            result_section.update(section)

    # Done
    return parsed_docs[0], parsed_docs[1], result_sections


def parse_class(cls: type) -> models.ClassDocs:
    """
    Given a class, parse its signature an docstring into a `ClassDocs` object.
    """

    # Parse the functions
    #
    # Make sure to add functions from base classes as well
    functions_by_name: dict[str, models.FunctionDocs] = {}

    def add_functions(cls: type) -> None:
        # Chain to the base classes
        for base in cls.__bases__:
            add_functions(base)

        # Then process this class. This way they override inherited functions.
        for name, func in inspect.getmembers(cls, inspect.isfunction):
            func_docs = parse_function(func)
            functions_by_name[name] = func_docs

    add_functions(cls)
    functions = list(functions_by_name.values())

    # Parse the fields
    fields_by_name: dict[str, models.ClassField] = {}

    for name, typ in inspection.get_resolved_type_annotations(cls).items():
        if typ is dataclasses.KW_ONLY:
            continue

        fields_by_name[name] = models.ClassField(
            name=name,
            type=str_type_hint(typ),
            default=None,
            description=None,
        )

    # Properties are also fields
    for name, _ in inspect.getmembers(cls, inspect.isdatadescriptor):
        if name in fields_by_name:
            continue

    # Is this a dataclass? If so, get the fields from there
    if is_dataclass(cls):
        for dataclass_field in dataclasses.fields(cls):
            doc_field = fields_by_name[dataclass_field.name]

            # Default value?
            if dataclass_field.default is not dataclasses.MISSING:
                doc_field.default = repr(dataclass_field.default)

            # Default factory?
            elif dataclass_field.default_factory is not dataclasses.MISSING:
                doc_field.default = repr(dataclass_field.default_factory())

    # Parse the docstring
    (
        short_description,
        long_description,
        sections,
    ) = _parse_class_docstring_with_inheritance(
        cls,
        key_sections=["attributes"],
    )

    # Add any information learned about fields from the docstring
    raw_attributes = sections["attributes"]

    for field_name, field_details in raw_attributes.items():
        try:
            result_field = fields_by_name[field_name]
        except KeyError:
            revel.warning(
                f"The docstring for class `{cls.__name__}` mentions a field `{field_name}` that does not exist in the class."
            )
            continue

        result_field.description = field_details

    # If `__init__` is missing documentation for any parameters, try to copy the
    # values from matching fields.
    for func_docs in functions:
        if func_docs.name != "__init__":
            continue

        for param in func_docs.parameters:
            if param.description is not None:
                continue

            try:
                field = fields_by_name[param.name]
            except KeyError:
                continue

            param.description = field.description

        break

    # Build the result
    return models.ClassDocs(
        name=cls.__name__,
        attributes=list(fields_by_name.values()),
        functions=functions,
        summary=short_description,
        details=long_description,
    )
