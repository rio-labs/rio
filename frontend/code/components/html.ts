import { getElementDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';

export type HtmlState = ComponentState & {
    _type_: 'Html-builtin';
    html?: string;
};

export class HtmlComponent extends ComponentBase {
    state: Required<HtmlState>;

    private containerElement: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');

        this.containerElement = document.createElement('div');
        element.appendChild(this.containerElement);

        return element;
    }

    updateElement(
        deltaState: HtmlState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.html !== undefined) {
            this.containerElement.innerHTML = deltaState.html;

            [this.naturalWidth, this.naturalHeight] = getElementDimensions(
                this.containerElement
            );
            this.makeLayoutDirty();
        }
    }
}
