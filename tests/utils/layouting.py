from __future__ import annotations

import typing as t

import rio.data_models
from rio.debug.layouter import Layouter
from rio.testing import BrowserClient

__all__ = ["verify_layout"]


async def verify_layout(build: t.Callable[[], rio.Component]) -> Layouter:
    """
    Rio contains two layout implementations: One on the client side, which
    determines the real layout of components, and a second one on the server
    side which is used entirely for testing.

    This function verifies that the results from the two layouters are the same.
    """
    async with BrowserClient(build) as client:
        layouter = await Layouter.create(client.session)

    for component_id, layout_should in layouter._layouts_should.items():
        layout_is = layouter._layouts_are[component_id]

        differences = list[str]()
        for attribute in rio.data_models.ComponentLayout.__annotations__:
            # Not all attributes are meant to be compared
            if attribute == "parent_id":
                continue

            value_should = getattr(layout_should, attribute)
            value_is = getattr(layout_is, attribute)

            difference = abs(value_is - value_should)
            if difference > 0.2:
                differences.append(f"{attribute}: {value_is} != {value_should}")

        if differences:
            component = layouter.get_component_by_id(component_id)
            raise ValueError(
                f"Layout of component {component} is incorrect:\n- "
                + "\n- ".join(differences)
            )

    return layouter
