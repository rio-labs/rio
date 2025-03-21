import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type SeparatorListItemState = ComponentState & {
    _type_: "SeparatorListItem-builtin";
};

export class SeparatorListItemComponent extends ComponentBase<SeparatorListItemState> {
    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-separator-list-item");
        return element;
    }
}
