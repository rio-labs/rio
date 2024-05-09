import pytest

import imy.docstrings

import rio.docs


def _create_tests():
    for obj, docs in rio.docs.find_documented_objects(postprocess=True):
        if isinstance(docs, imy.docstrings.FunctionDocs):

            class Tests:  # type: ignore
                def test_summary(self) -> None:
                    assert docs.summary is not None

                def test_details(self) -> None:
                    assert docs.details is not None

                @pytest.mark.parametrize(
                    "param",
                    docs.parameters,
                    ids=[param.name for param in docs.parameters],
                )
                def test_param_description(
                    self, param: imy.docstrings.FunctionParameter
                ) -> None:
                    assert param.description is not None

            name = f"Test_{docs.name}"
        else:
            assert isinstance(obj, type)

            methods = [
                func
                for func in docs.functions
                if func.name != "__init__" or not issubclass(obj, rio.Component)
            ]
            parametrize_methods = pytest.mark.parametrize(
                "method",
                methods,
                ids=[method.name for method in methods],
            )

            class Tests:
                def test_summary(self) -> None:
                    assert docs.summary is not None

                def test_details(self) -> None:
                    assert docs.details is not None

                @pytest.mark.parametrize(
                    "attr",
                    docs.attributes,
                    ids=[attr.name for attr in docs.attributes],
                )
                def test_attr_description(
                    self, attr: imy.docstrings.ClassField
                ) -> None:
                    assert attr.description is not None

                @parametrize_methods
                def test_method_summary(
                    self, method: imy.docstrings.FunctionDocs
                ) -> None:
                    assert method.summary is not None

                @parametrize_methods
                def test_method_details(
                    self, method: imy.docstrings.FunctionDocs
                ) -> None:
                    assert method.details is not None

                @parametrize_methods
                def test_method_parameters(
                    self, method: imy.docstrings.FunctionDocs
                ) -> None:
                    for param in method.parameters:
                        assert (
                            param.description is not None
                        ), f"Parameter {param.name!r} has no description"

            name = f"Test{docs.name}"

        globals()[name] = Tests


_create_tests()
