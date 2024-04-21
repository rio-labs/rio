import { ComponentBase, ComponentState } from './componentBase';
import { LayoutContext } from '../layouting';
import { Color } from '../dataModels';
import { getTextDimensions } from '../layoutHelpers';
import { colorToCssString } from '../cssUtils';

export type NodeInputState = ComponentState & {
    _type_: 'NodeInput-builtin';
    name: string;
    color: Color;
    key: string;
};

export class NodeInputComponent extends ComponentBase {
    state: Required<NodeInputState>;

    textElement: HTMLElement;
    circleElement: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-node-editor-port', 'rio-node-editor-input');

        element.innerHTML = `
            <div class="rio-node-editor-port-circle"></div>
            <div class="rio-node-editor-port-text"></div>
        `;

        this.textElement = element.querySelector(
            '.rio-node-editor-port-text'
        ) as HTMLElement;

        this.circleElement = element.querySelector(
            '.rio-node-editor-port-circle'
        ) as HTMLElement;

        return element;
    }

    updateElement(
        deltaState: NodeInputState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Name
        if (deltaState.name !== undefined) {
            this.textElement.textContent = deltaState.name;

            // Cache the dimensions
            let textDimensions = getTextDimensions(deltaState.name, 'text');
            this.naturalWidth = textDimensions[0];
            this.naturalHeight = textDimensions[1];
        }

        // Color
        if (deltaState.color !== undefined) {
            this.element.style.setProperty(
                '--port-color',
                colorToCssString(deltaState.color)
            );
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {}

    updateNaturalHeight(ctx: LayoutContext): void {}
}
