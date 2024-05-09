import pytest

import imy.docstrings

import rio.docs


def _create_tests():
    for obj, docs in rio.docs.find_documented_objects(postprocess=True):
        if isinstance(docs, imy.docstrings.FunctionDocs):
            test_cls = _create_function_tests(docs)
        else:
            assert isinstance(obj, type)
            test_cls = _create_class_tests(obj, docs)

        globals()[test_cls.__name__] = test_cls


def _create_function_tests(docs: imy.docstrings.FunctionDocs) -> type:
    class Tests:  # type: ignore
        def test_summary(self) -> None:
            assert docs.summary is not None, f"{docs.name} has no summary"

        def test_details(self) -> None:
            assert docs.details is not None, f"{docs.name} has no details"

        @pytest.mark.parametrize(
            "param",
            docs.parameters,
            ids=[param.name for param in docs.parameters],
        )
        def test_param_description(
            self, param: imy.docstrings.FunctionParameter
        ) -> None:
            assert (
                param.description is not None
            ), f"{docs.name}.{param.name} has no description"

    Tests.__name__ = f"Test_{docs.name}"
    return Tests


def _create_class_tests(cls: type, docs: imy.docstrings.ClassDocs) -> type:
    methods = [
        func
        for func in docs.functions
        if func.name != "__init__" or not issubclass(cls, rio.Component)
    ]
    parametrize_methods = pytest.mark.parametrize(
        "method",
        methods,
        ids=[method.name for method in methods],
    )

    class Tests:
        def test_summary(self) -> None:
            assert docs.summary is not None, f"{cls.__name__} has no summary"

        def test_details(self) -> None:
            assert docs.details is not None, f"{cls.__name__} has no details"

        @pytest.mark.parametrize(
            "attr",
            docs.attributes,
            ids=[attr.name for attr in docs.attributes],
        )
        def test_attr_description(
            self, attr: imy.docstrings.ClassField
        ) -> None:
            assert (
                attr.description is not None
            ), f"{cls.__name__}.{attr.name} has no description"

        @parametrize_methods
        def test_method_summary(
            self, method: imy.docstrings.FunctionDocs
        ) -> None:
            assert (
                method.summary is not None
            ), f"{cls.__name__}.{method.name} has no summary"

        @parametrize_methods
        def test_method_details(
            self, method: imy.docstrings.FunctionDocs
        ) -> None:
            assert (
                method.details is not None
            ), f"{cls.__name__}.{method.name} has no details"

        @parametrize_methods
        def test_method_parameters(
            self, method: imy.docstrings.FunctionDocs
        ) -> None:
            for param in method.parameters[1:]:
                assert (
                    param.description is not None
                ), f"Parameter {param.name!r} has no description"

    Tests.__name__ = f"Test{docs.name}"
    return Tests


_create_tests()
