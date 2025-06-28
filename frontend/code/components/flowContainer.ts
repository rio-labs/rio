import {
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type FlowState = ComponentState & {
    _type_: "FlowContainer-builtin";
    children: ComponentId[];
    row_spacing: number;
    column_spacing: number;
    justify: "left" | "center" | "right" | "justify" | "grow";
};

export class FlowComponent extends ComponentBase<FlowState> {
    private innerElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-flow-container");

        this.innerElement = document.createElement("div");
        this.innerElement.classList.add("rio-flow-inner");
        element.appendChild(this.innerElement);

        return element;
    }

    updateElement(
        deltaState: DeltaState<FlowState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.row_spacing !== undefined) {
            this.innerElement.style.rowGap = `${deltaState.row_spacing}rem`;
        }

        if (deltaState.column_spacing !== undefined) {
            this.innerElement.style.columnGap = `${deltaState.column_spacing}rem`;
        }

        if (deltaState.justify !== undefined) {
            this.innerElement.style.justifyContent = {
                left: "start",
                right: "end",
                center: "center",
                justify: "space-between",
                grow: "stretch",
            }[deltaState.justify];
        }

        if (deltaState.children !== undefined) {
            this.replaceChildren(
                context,
                deltaState.children,
                this.innerElement,
                true
            );
            this.updateChildGrows(
                deltaState.children,
                deltaState.justify ?? this.state.justify
            );
        }
    }

    onChildGrowChanged(): void {
        this.updateChildGrows(this.state.children, this.state.justify);
    }

    private updateChildGrows(children: ComponentId[], justify: string): void {
        // Set the children's `flex-grow`
        let hasGrowers = false;
        for (let [index, childId] of children.entries()) {
            let childComponent = componentsById[childId]!;
            let childWrapper = this.innerElement.children[index] as HTMLElement;

            if (childComponent.state._grow_[0]) {
                hasGrowers = true;
                childWrapper.style.flexGrow = "1";
            } else {
                childWrapper.style.flexGrow = "0";
            }
        }

        // If nobody wants to grow, all of them do
        if (justify === "grow" && !hasGrowers) {
            for (let childWrapper of this.innerElement.children) {
                (childWrapper as HTMLElement).style.flexGrow = "1";
            }
        }
    }
}
