import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentId } from "../dataModels";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type HighLevelComponentState = ComponentState & {
    _type_: "HighLevelComponent-builtin";
    _child_: ComponentId;
};

export class HighLevelComponent extends ComponentBase<HighLevelComponentState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-high-level-component");
        return element;
    }

    updateElement(
        deltaState: DeltaState<HighLevelComponentState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(context, deltaState._child_);
    }
}
