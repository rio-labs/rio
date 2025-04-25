import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { Color } from "../dataModels";
import { colorToCssString } from "../cssUtils";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type NodeOutputState = ComponentState & {
    _type_: "NodeOutput-builtin";
    name: string;
    color: Color;
    key: string;
};

export class NodeOutputComponent extends ComponentBase<NodeOutputState> {
    textElement: HTMLElement;
    circleElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add(
            "rio-graph-editor-port",
            "rio-graph-editor-output"
        );

        element.innerHTML = `
            <div class="rio-graph-editor-port-circle"></div>
            <div class="rio-graph-editor-port-text"></div>
        `;

        this.textElement = element.querySelector(
            ".rio-graph-editor-port-text"
        ) as HTMLElement;

        this.circleElement = element.querySelector(
            ".rio-graph-editor-port-circle"
        ) as HTMLElement;

        return element;
    }

    updateElement(
        deltaState: DeltaState<NodeOutputState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Name
        if (deltaState.name !== undefined) {
            this.textElement.textContent = deltaState.name;
        }

        // Color
        if (deltaState.color !== undefined) {
            this.element.style.setProperty(
                "--port-color",
                colorToCssString(deltaState.color)
            );
        }
    }
}
