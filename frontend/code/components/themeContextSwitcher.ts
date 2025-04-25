import { applySwitcheroo } from "../designApplication";
import { ColorSet, ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type ThemeContextSwitcherState = ComponentState & {
    _type_: "ThemeContextSwitcher-builtin";
    content: ComponentId;
    color: ColorSet;
};

export class ThemeContextSwitcherComponent extends ComponentBase<ThemeContextSwitcherState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-single-container");
        return element;
    }

    updateElement(
        deltaState: DeltaState<ThemeContextSwitcherState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the child
        this.replaceOnlyChild(context, deltaState.content);

        // Colorize
        if (deltaState.color !== undefined) {
            applySwitcheroo(this.element, deltaState.color);
        }
    }
}
