import { ComponentBase, ComponentState } from "./componentBase";

export type WebsiteState = ComponentState & {
    _type_: "Website-builtin";
    url?: string;
};

export class WebsiteComponent extends ComponentBase {
    declare state: Required<WebsiteState>;
    element: HTMLIFrameElement;

    createElement(): HTMLElement {
        let element = document.createElement("iframe");
        element.classList.add("rio-website");
        return element;
    }

    updateElement(
        deltaState: WebsiteState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (
            deltaState.url !== undefined &&
            deltaState.url !== this.element.src
        ) {
            this.element.src = deltaState.url;
        }
    }
}
