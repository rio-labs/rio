import { ComponentStatesUpdateContext } from "../componentManagement";
import { applyIcon } from "../designApplication";
import { PressableElement } from "../elements/pressableElement";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type SwitchState = ComponentState & {
    _type_: "Switch-builtin";
    is_on: boolean;
    is_sensitive: boolean;
};

export class SwitchComponent extends ComponentBase<SwitchState> {
    pressableElement: PressableElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-switch");
        element.role = "checkbox";

        // Switches don't grow, so we need a helper element that will be
        // centered.
        this.pressableElement = new PressableElement({ role: "checkbox" });
        this.pressableElement.onPress = this.onPress.bind(this);
        element.appendChild(this.pressableElement);

        let knobElement = document.createElement("div");
        knobElement.classList.add("knob");
        this.pressableElement.appendChild(knobElement);

        applyIcon(knobElement, "material/check_small", "var(--icon-color)");

        return element;
    }

    updateElement(
        deltaState: DeltaState<SwitchState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.is_on !== undefined) {
            this.element.classList.toggle("is-on", deltaState.is_on);
            this.pressableElement.ariaChecked = deltaState.is_on
                ? "true"
                : "false";
        }

        if (deltaState.is_sensitive !== undefined) {
            this.element.classList.toggle(
                "rio-switcheroo-disabled",
                !deltaState.is_sensitive
            );

            this.pressableElement.isSensitive = deltaState.is_sensitive;
        }
    }

    private onPress(): void {
        this.setStateAndNotifyBackend({
            is_on: !this.state.is_on,
        });
    }
}
