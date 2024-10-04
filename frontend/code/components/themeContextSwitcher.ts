import { applySwitcheroo } from "../designApplication";
import { ColorSet, ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";

export type ThemeContextSwitcherState = ComponentState & {
    _type_: "ThemeContextSwitcher-builtin";
    content?: ComponentId;
    color?: ColorSet;
};

export class ThemeContextSwitcherComponent extends ComponentBase {
    declare state: Required<ThemeContextSwitcherState>;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-single-container");
        return element;
    }

    updateElement(
        deltaState: ThemeContextSwitcherState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the child
        this.replaceOnlyChild(latentComponents, deltaState.content);

        // Colorize
        if (deltaState.color !== undefined) {
            applySwitcheroo(this.element, deltaState.color);
        }
    }
}
