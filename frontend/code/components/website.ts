import { ComponentBase, ComponentState } from './componentBase';

export type WebsiteState = ComponentState & {
    _type_: 'Website-builtin';
    url?: string;
};

export class WebsiteComponent extends ComponentBase {
    state: Required<WebsiteState>;
    element: HTMLIFrameElement;

    createElement(): HTMLElement {
        return document.createElement('iframe');
    }

    updateElement(
        deltaState: WebsiteState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (
            deltaState.url !== undefined &&
            deltaState.url !== this.element.src
        ) {
            this.element.src = deltaState.url;
        }
    }
}
