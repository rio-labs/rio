import { devToolsConnector } from "../app";
import { applyIcon } from "../designApplication";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type ComponentPickerState = ComponentState & {
    _type_: "ComponentPicker-builtin";
};

export class ComponentPickerComponent extends ComponentBase<ComponentPickerState> {
    protected createElement(
        context: ComponentStatesUpdateContext
    ): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-component-picker");

        applyIcon(element, "material/arrow_selector_tool:fill");

        element.addEventListener("click", this.pickComponent.bind(this));

        return element;
    }

    async pickComponent() {
        this.element.classList.add("active");

        await devToolsConnector!.pickComponent();

        this.element.classList.remove("active");
    }
}
