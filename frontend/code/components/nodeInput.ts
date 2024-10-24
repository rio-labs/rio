import { ComponentBase, ComponentState } from "./componentBase";
import { Color } from "../dataModels";
import { colorToCssString } from "../cssUtils";

export type NodeInputState = ComponentState & {
    _type_: "NodeInput-builtin";
    name: string;
    color: Color;
    key: string;
};

export class NodeInputComponent extends ComponentBase {
    declare state: Required<NodeInputState>;

    textElement: HTMLElement;
    circleElement: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-node-editor-port", "rio-node-editor-input");

        element.innerHTML = `
            <div class="rio-node-editor-port-circle"></div>
            <div class="rio-node-editor-port-text"></div>
        `;

        this.textElement = element.querySelector(
            ".rio-node-editor-port-text"
        ) as HTMLElement;

        this.circleElement = element.querySelector(
            ".rio-node-editor-port-circle"
        ) as HTMLElement;

        return element;
    }

    updateElement(
        deltaState: NodeInputState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

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
