import { Color } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { colorToCssString } from "../cssUtils";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type SeparatorState = ComponentState & {
    _type_: "Separator-builtin";
    orientation: "horizontal" | "vertical";
    color: Color;
};

export class SeparatorComponent extends ComponentBase<SeparatorState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-separator");
        return element;
    }

    updateElement(
        deltaState: DeltaState<SeparatorState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Color
        if (deltaState.color === undefined) {
            // Nothing to do
        }
        // If nothing was specified, use a color from the theme
        else if (deltaState.color === null) {
            this.element.style.setProperty(
                "--separator-color",
                "var(--rio-local-text-color)"
            );
            this.element.style.setProperty("--separator-opacity", "0.3");
        }
        // Use the provided color
        else {
            this.element.style.setProperty(
                "--separator-color",
                colorToCssString(deltaState.color)
            );
            this.element.style.setProperty("--separator-opacity", "1");
        }
    }
}
