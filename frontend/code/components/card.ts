import { applySwitcheroo } from "../designApplication";
import { ColorSet, ComponentId } from "../dataModels";
import { RippleEffect } from "../rippleEffect";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { markEventAsHandled } from "../eventHandling";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type CardState = ComponentState & {
    _type_: "Card-builtin";
    content: ComponentId;
    corner_radius: number | [number, number, number, number];
    reportPress: boolean;
    ripple: boolean;
    elevate_on_hover: boolean;
    colorize_on_hover: boolean;
    color: ColorSet;
};

export class CardComponent extends ComponentBase<CardState> {
    // If this card has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;
    private rippleCss: { [attr: string]: string } = {};

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the element
        let element = document.createElement("div");
        element.classList.add("rio-card");

        // Detect presses
        element.onclick = (event) => {
            // Is the backend interested in presses?
            if (!this.state.reportPress) {
                return;
            }

            // The event was handled. Stop it from propagating further.
            markEventAsHandled(event);

            // Notify the backend
            this.sendMessageToBackend({});
        };

        return element;
    }

    updateElement(
        deltaState: DeltaState<CardState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the child
        this.replaceOnlyChild(context, deltaState.content);

        // Update the corner radius
        if (deltaState.corner_radius !== undefined) {
            let borderRadius =
                typeof deltaState.corner_radius === "number"
                    ? `${deltaState.corner_radius}rem`
                    : `${deltaState.corner_radius[0]}rem ${deltaState.corner_radius[1]}rem ${deltaState.corner_radius[2]}rem ${deltaState.corner_radius[3]}rem`;

            this.element.style.borderRadius = borderRadius;
            this.rippleCss["borderRadius"] = borderRadius;

            if (this.rippleInstance !== null) {
                this.rippleInstance.customCss = this.rippleCss;
            }
        }

        // Report presses?
        if (deltaState.reportPress === true) {
            this.element.style.cursor = "pointer";
        } else if (deltaState.reportPress === false) {
            this.element.style.removeProperty("cursor");
        }

        // Elevate on hover
        if (deltaState.elevate_on_hover === true) {
            this.element.classList.add("rio-card-elevate-on-hover");
        } else if (deltaState.elevate_on_hover === false) {
            this.element.classList.remove("rio-card-elevate-on-hover");
        }

        // Colorize on hover
        if (deltaState.colorize_on_hover === true) {
            this.element.classList.add("rio-card-colorize-on-hover");
        } else if (deltaState.colorize_on_hover === false) {
            this.element.classList.remove("rio-card-colorize-on-hover");
        }

        // Ripple
        if (deltaState.ripple === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(this.element, {
                    customCss: this.rippleCss,
                });
            }
        } else if (deltaState.ripple === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;
            }
        }

        // Colorize
        if (deltaState.color !== undefined) {
            applySwitcheroo(this.element, deltaState.color);
        }
    }
}
