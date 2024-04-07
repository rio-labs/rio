import { ComponentBase, ComponentState } from './componentBase';

export type HtmlState = ComponentState & {
    _type_: 'Html-builtin';
    html?: string;
};

export class HtmlComponent extends ComponentBase {
    state: Required<HtmlState>;

    createElement(): HTMLElement {
        return document.createElement('div');
    }

    updateElement(
        deltaState: HtmlState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.html !== undefined) {
            this.element.innerHTML = deltaState.html;
        }
    }
}
