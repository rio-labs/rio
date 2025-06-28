import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentId } from "../dataModels";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type ClassContainerState = ComponentState & {
    _type_: "ClassContainer-builtin";
    content: ComponentId | null;
    classes: string[];
};

export class ClassContainerComponent extends ComponentBase<ClassContainerState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        return document.createElement("div");
    }

    updateElement(
        deltaState: DeltaState<ClassContainerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(context, deltaState.content);

        if (deltaState.classes !== undefined) {
            // Remove all old values
            this.element.className = "rio-component rio-class-container";

            // Add all new values
            this.element.classList.add(...deltaState.classes);
        }
    }
}
