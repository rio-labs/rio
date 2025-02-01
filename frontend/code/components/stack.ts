import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";

export type StackState = ComponentState & {
    _type_: "Stack-builtin";
    children?: ComponentId[];
};

export class StackComponent extends ComponentBase {
    declare state: Required<StackState>;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-stack");
        return element;
    }

    updateElement(
        deltaState: StackState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // For some reason, a CSS `grid` seems to squish children to their minimum size.
        // Wrapping each child in a container element fixes this, somehow.
        this.replaceChildren(
            latentComponents,
            deltaState.children,
            this.element,
            true
        );
    }
}
