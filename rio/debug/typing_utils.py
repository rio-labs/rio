import types
from dataclasses import dataclass
from typing import *  # type: ignore

import introspection.typing

__all__ = ["ScopedAnnotation"]


@dataclass
class ScopedAnnotation:
    annotation: introspection.types.TypeAnnotation
    module: types.ModuleType

    def evaluate(self) -> introspection.types.TypeAnnotation:
        return introspection.typing.resolve_forward_refs(
            self.annotation,
            self.module,
            mode="eval",
            strict=False,
            treat_name_errors_as_imports=True,
        )
