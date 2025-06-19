import { ComponentStatesUpdateContext } from "../componentManagement";
import { applyIcon } from "../designApplication";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type CheckboxState = ComponentState & {
    _type_: "Checkbox-builtin";
    is_on: boolean;
    is_sensitive: boolean;
};

export class CheckboxComponent extends ComponentBase<CheckboxState> {
    private checkboxElement: HTMLInputElement;
    private borderElement: HTMLElement;
    private checkElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-checkbox");

        // Use an actual checkbox input for semantics. This helps e.g. screen
        // readers to understand the element.
        this.checkboxElement = document.createElement("input");
        this.checkboxElement.type = "checkbox";
        element.appendChild(this.checkboxElement);

        // This will display a border around the checkbox at all times
        this.borderElement = document.createElement("div");
        this.borderElement.classList.add("rio-checkbox-border");
        element.appendChild(this.borderElement);

        // This will display a check mark when the checkbox is on
        this.checkElement = document.createElement("div");
        this.checkElement.classList.add("rio-checkbox-check");
        element.appendChild(this.checkElement);

        // Initialize the icons
        applyIcon(
            this.checkElement,
            "material/check_small",
            "var(--rio-local-bg)"
        );

        // Listen for changes to the checkbox state
        this.checkboxElement.addEventListener("change", () => {
            this.setStateAndNotifyBackend({
                is_on: this.checkboxElement.checked,
            });
        });

        // Stop press propagation but don't prevent default behavior, so the
        // checkbox can still be toggled
        element.onclick = (event) => {
            event.stopPropagation();
            event.stopImmediatePropagation();
        };

        return element;
    }

    updateElement(
        deltaState: DeltaState<CheckboxState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.is_on !== undefined) {
            if (deltaState.is_on) {
                this.element.classList.add("is-on");
            } else {
                this.element.classList.remove("is-on");
            }

            // Assign the new value to the checkbox element, but only if it
            // differs from the current value, to avoid immediately triggering
            // the event again.
            if (this.checkboxElement.checked !== deltaState.is_on) {
                this.checkboxElement.checked = deltaState.is_on;
            }
        }

        if (deltaState.is_sensitive === true) {
            this.element.classList.remove("rio-disabled-input");
            this.checkboxElement.disabled = false;
        } else if (deltaState.is_sensitive === false) {
            this.element.classList.add("rio-disabled-input");
            this.checkboxElement.disabled = true;
        }
    }
}
