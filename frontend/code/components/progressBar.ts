import { ComponentStatesUpdateContext } from "../componentManagement";
import { ColorSet } from "../dataModels";
import { applySwitcheroo } from "../designApplication";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type ProgressBarState = ComponentState & {
    _type_: "ProgressBar-builtin";
    progress: number | null;
    color: ColorSet;
    rounded: boolean;
};

export class ProgressBarComponent extends ComponentBase<ProgressBarState> {
    fillElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-progress-bar");

        element.innerHTML = `
            <div class="rio-progress-bar-fill"></div>
            <div class="rio-progress-bar-track"></div>
        `;

        this.fillElement = element.querySelector(
            ".rio-progress-bar-fill"
        ) as HTMLElement;

        return element;
    }

    updateElement(
        deltaState: DeltaState<ProgressBarState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.progress !== undefined) {
            // Indeterminate progress
            if (deltaState.progress === null) {
                this.element.classList.add("rio-progress-bar-indeterminate");
            }

            // Known progress
            else {
                let progress = Math.max(0, Math.min(1, deltaState.progress));

                this.element.style.setProperty(
                    "--rio-progress-bar-fraction",
                    `${progress * 100}%`
                );
                this.element.classList.remove("rio-progress-bar-indeterminate");
            }
        }

        // Apply the color
        //
        // Only apply it to the fill element, so that the track doesn't change
        // color as well.
        if (deltaState.color !== undefined) {
            applySwitcheroo(
                this.fillElement,
                deltaState.color === "keep" ? "bump" : deltaState.color
            );
        }

        // Round the corners?
        if (deltaState.rounded === true) {
            this.element.style.setProperty(
                "border-radius",
                "var(--rio-global-corner-radius-small)"
            );
        } else if (deltaState.rounded === false) {
            this.element.style.removeProperty("border-radius");
        }
    }
}
