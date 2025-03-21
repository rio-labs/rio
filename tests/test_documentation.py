import enum
import re
import textwrap
import typing as t

import imy.docstrings
import pytest

import rio.docs
from tests.utils.ruff import ruff_check, ruff_format


def parametrize_with_name(
    param_name: str,
    docs: t.Iterable[
        imy.docstrings.FunctionDocs
        | imy.docstrings.ClassDocs
        | imy.docstrings.AttributeDocs
        | imy.docstrings.ParameterDocs
    ],
):
    def decorator(func):
        return pytest.mark.parametrize(
            param_name,
            docs,
            ids=[doc.name for doc in docs],
        )(func)

    return decorator


def _create_tests() -> None:
    for docs in rio.docs.get_toplevel_documented_objects().values():
        test_cls = _create_tests_for(docs)
        globals()[test_cls.__name__] = test_cls


def _create_tests_for(
    docs: imy.docstrings.ClassDocs | imy.docstrings.FunctionDocs,
) -> type:
    if isinstance(docs, imy.docstrings.FunctionDocs):
        cls = _create_function_tests(docs)
    else:
        cls = _create_class_tests(docs)

    cls.__name__ = _get_name_for_test_class(docs)
    return cls


def _get_name_for_test_class(
    docs: imy.docstrings.FunctionDocs | imy.docstrings.ClassDocs,
) -> str:
    return "Test<" + docs.full_name.removeprefix("rio.").replace(".", "_") + ">"


CODE_BLOCK_PATTERN = re.compile(r"```(.*?)```", flags=re.DOTALL)


def _get_code_blocks(docstring: str | None) -> list[str]:
    """
    Returns a list of all code blocks in the docstring of a component.
    """
    # No docs?
    if not docstring:
        return []

    docstring = textwrap.dedent(docstring)

    # Find any contained code blocks
    result: list[str] = []
    for match in CODE_BLOCK_PATTERN.finditer(docstring):
        block: str = match.group(1)

        # Split into language and source
        linebreak = block.find("\n")
        assert linebreak != -1
        language = block[:linebreak]
        block = block[linebreak + 1 :]

        # Make sure a language is specified
        assert language, "The code block has no language specified"

        if language in ("py", "python"):
            result.append(block)

    return result


def _create_tests_for_docstring(
    docs: imy.docstrings.ClassDocs
    | imy.docstrings.FunctionDocs
    | imy.docstrings.PropertyDocs,
) -> type:
    code_blocks = _get_code_blocks(docs.summary)
    code_blocks += _get_code_blocks(docs.details)

    code_block_ids = [f"code block {nr}" for nr, _ in enumerate(code_blocks, 1)]

    class DocstringTests:
        # __init__ methods don't need a summary or details
        if docs.name != "__init__":

            def test_summary(self) -> None:
                assert docs.summary is not None, f"{docs.name} has no summary"

            def test_details(self) -> None:
                assert docs.details is not None, f"{docs.name} has no details"

        @pytest.mark.parametrize("code", code_blocks, ids=code_block_ids)
        def test_code_block_is_formatted(self, code: str) -> None:
            # Make sure all code blocks are formatted according to ruff
            formatted_code = ruff_format(code)

            # Ruff often inserts 2 empty lines between definitions, but that's
            # really not necessary in docstrings. Collapse them to a single
            # empty line.
            code = code.replace("\n\n\n", "\n\n")
            formatted_code = formatted_code.replace("\n\n\n", "\n\n")

            assert formatted_code == code

        @pytest.mark.parametrize("code", code_blocks, ids=code_block_ids)
        def test_analyze_code_block(self, code: str) -> None:
            # A lot of snippets are missing context, so it's only natural that
            # ruff will find issues with the code. There isn't really anything
            # we can do about it, so we'll just skip those objects.
            if docs.object in (
                rio.Color,
                rio.UserSettings,
            ):
                pytest.xfail()

            errors = ruff_check(code)
            assert not errors, errors

    return DocstringTests


def _create_function_tests(docs: imy.docstrings.FunctionDocs) -> type:
    # If the function is a decorator, there's no need to document that it takes
    # a function/class as an argument
    if docs.metadata.decorator and list(docs.parameters) == ["handler"]:
        parameters = []
    elif docs.has_implicit_first_parameter:
        parameters = list(docs.parameters.values())[1:]
    else:
        parameters = docs.parameters.values()

    DocstringTests = _create_tests_for_docstring(docs)

    class FunctionTests(DocstringTests):
        def test_parameters_are_all_public(self) -> None:
            private_params = [
                param.name for param in parameters if param.name.startswith("_")
            ]
            assert not private_params, (
                f"These parameters should be private: {private_params}"
            )

        def test_parameter_descriptions(self) -> None:
            params_without_description = [
                param.name for param in parameters if not param.description
            ]
            assert not params_without_description, (
                f"These parameters have no description: {params_without_description}"
            )

    return FunctionTests


def _create_property_tests(docs: imy.docstrings.PropertyDocs) -> type:
    DocstringTests = _create_tests_for_docstring(docs)

    class PropertyTests(DocstringTests):
        pass

    return PropertyTests


def _create_class_tests(docs: imy.docstrings.ClassDocs) -> type:
    # Components only need their constructor documented, attributes don't matter
    attributes = (
        []
        if issubclass(docs.object, rio.Component)
        else docs.attributes.values()
    )

    DocstringTests = _create_tests_for_docstring(docs)

    class ClassTests(DocstringTests):
        # Event and Error classes shouldn't be instantiated by the user, so make
        # sure their constructor is marked as private
        if docs.name.endswith("Event") or issubclass(
            docs.object, BaseException
        ):

            def test_constructor_is_private(self):
                assert "__init__" not in docs.members, (
                    f"Constructor of {docs.name} is not marked as private"
                )

        def test_attributes_are_all_public(self):
            private_attrs = [
                attr.name
                for attr in docs.attributes.values()
                if attr.name.startswith("_")
            ]
            assert not private_attrs, (
                f"These attributes should be private: {private_attrs}"
            )

        @parametrize_with_name("attr", attributes)
        def test_attribute_description(
            self, attr: imy.docstrings.AttributeDocs
        ) -> None:
            assert attr.description is not None, (
                f"Attribute {attr.name!r} has no details"
            )

        # Create tests for all members of this class
        for member in docs.members.values():
            if isinstance(member, imy.docstrings.FunctionDocs):
                # Ignore the constructor of Enums
                if member.name == "__init__" and issubclass(
                    docs.object, enum.Enum
                ):
                    continue

                test = _create_function_tests(member)
            elif isinstance(member, imy.docstrings.PropertyDocs):
                test = _create_property_tests(member)
            else:
                raise Exception(
                    f"Don't know how to create tests for a {type(member).__name__} object"
                )

            test.__name__ = f"Test<{member.name}>"
            vars()[test.__name__] = test

    return ClassTests


_create_tests()
