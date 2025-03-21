import { Color } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { colorToCssString } from "../cssUtils";

export type SeparatorState = ComponentState & {
    _type_: "Separator-builtin";
    orientation: "horizontal" | "vertical";
    color: Color;
};

export class SeparatorComponent extends ComponentBase<SeparatorState> {
    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-separator");
        return element;
    }

    updateElement(
        deltaState: DeltaState<SeparatorState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

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
