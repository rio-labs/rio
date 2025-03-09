import { RippleEffect } from "../rippleEffect";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentId } from "../dataModels";

export type CustomListItemState = ComponentState & {
    _type_: "CustomListItem-builtin";
    content: ComponentId;
    pressable: boolean;
};

export class CustomListItemComponent extends ComponentBase<CustomListItemState> {
    // If this item has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-custom-list-item");
        return element;
    }

    updateElement(
        deltaState: DeltaState<CustomListItemState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the child
        this.replaceOnlyChild(latentComponents, deltaState.content);

        // Style the surface depending on whether it is pressable
        if (deltaState.pressable === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(this.element);

                this.element.style.cursor = "pointer";
                this.element.style.setProperty(
                    "--hover-color",
                    "var(--rio-local-bg-active)"
                );

                this.element.onclick = this._on_press.bind(this);
            }
        } else if (deltaState.pressable === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;

                this.element.style.removeProperty("cursor");
                this.element.style.setProperty("--hover-color", "transparent");

                this.element.onclick = null;
            }
        }
    }

    private _on_press(): void {
        this.sendMessageToBackend({
            type: "press",
        });
    }
}
