import { getRootComponent } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";

export type OverlayState = ComponentState & {
    _type_: "Overlay-builtin";
    content?: ComponentId;
};

export class OverlayComponent extends ComponentBase {
    declare state: Required<OverlayState>;

    private overlayContentElement: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-overlay");

        this.overlayContentElement = document.createElement("div");
        this.overlayContentElement.classList.add("rio-overlay-content");
        this.overlayContentElement.dataset.ownerId = `${this.id}`;

        requestAnimationFrame(() => {
            getRootComponent().userOverlaysContainer.appendChild(
                this.overlayContentElement
            );
        });

        return element;
    }

    onDestruction(): void {
        super.onDestruction();
        this.overlayContentElement.remove();
    }

    updateElement(
        deltaState: OverlayState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.overlayContentElement
        );
    }
}
