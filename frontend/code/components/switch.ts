import { applyIcon } from "../designApplication";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type SwitchState = ComponentState & {
    _type_: "Switch-builtin";
    is_on: boolean;
    is_sensitive: boolean;
};

export class SwitchComponent extends ComponentBase<SwitchState> {
    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-switch");

        let containerElement = document.createElement("div");
        element.appendChild(containerElement);

        let checkboxElement = document.createElement("input");
        checkboxElement.type = "checkbox";
        containerElement.appendChild(checkboxElement);

        let knobElement = document.createElement("div");
        knobElement.classList.add("knob");
        containerElement.appendChild(knobElement);

        checkboxElement.addEventListener("change", () => {
            this.setStateAndNotifyBackend({
                is_on: checkboxElement.checked,
            });
        });

        applyIcon(knobElement, "material/check_small", "var(--icon-color)");

        return element;
    }

    updateElement(
        deltaState: DeltaState<SwitchState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.is_on !== undefined) {
            if (deltaState.is_on) {
                this.element.classList.add("is-on");
            } else {
                this.element.classList.remove("is-on");
            }

            // Assign the new value to the checkbox element, but only if it
            // differs from the current value, to avoid immediately triggering
            // the event again.
            let checkboxElement = this.element.querySelector("input");
            if (checkboxElement?.checked !== deltaState.is_on) {
                checkboxElement!.checked = deltaState.is_on;
            }
        }

        if (deltaState.is_sensitive === true) {
            this.element.classList.remove("rio-switcheroo-disabled");
            let checkbox = this.element.querySelector("input");
            checkbox!.disabled = false;
        } else if (deltaState.is_sensitive === false) {
            this.element.classList.add("rio-switcheroo-disabled");
            let checkbox = this.element.querySelector("input");
            checkbox!.disabled = true;
        }
    }
}
