import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { Color } from "../dataModels";
import { colorToCssString } from "../cssUtils";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type NodeInputState = ComponentState & {
    _type_: "NodeInput-builtin";
    name: string;
    color: Color;
    key: string;
};

export class NodeInputComponent extends ComponentBase<NodeInputState> {
    textElement: HTMLElement;
    circleElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add(
            "rio-graph-editor-port",
            "rio-graph-editor-input"
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
        deltaState: DeltaState<NodeInputState>,
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
