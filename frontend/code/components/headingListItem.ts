import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { textStyleToCss } from "../cssUtils";

export type HeadingListItemState = ComponentState & {
    _type_: "HeadingListItem-builtin";
    text: string;
};

export class HeadingListItemComponent extends ComponentBase<HeadingListItemState> {
    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement("div");
        element.classList.add("rio-heading-list-item");

        // Apply a style. This could be done with CSS, instead of doing it
        // individually for each component, but these are rare and this preempts
        // duplicate code.
        Object.assign(element.style, textStyleToCss("heading3"));

        return element;
    }

    updateElement(
        deltaState: DeltaState<HeadingListItemState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.text !== undefined) {
            this.element.textContent = deltaState.text;
        }
    }
}
