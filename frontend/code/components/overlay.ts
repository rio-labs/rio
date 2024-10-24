import { getRootComponent } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";

export type OverlayState = ComponentState & {
    _type_: "Overlay-builtin";
    content?: ComponentId;
};

export class OverlayComponent extends ComponentBase {
    declare state: Required<OverlayState>;

    private overlayElement: HTMLElement;

    createElement(): HTMLElement {
        this.overlayElement = document.createElement("div");
        this.overlayElement.classList.add("rio-overlay-content");
        this.overlayElement.dataset.ownerId = `${this.id}`;

        requestAnimationFrame(() => {
            getRootComponent().overlaysContainer.appendChild(
                this.overlayElement
            );
        });

        return document.createElement("div");
    }

    onDestruction(): void {
        super.onDestruction();
        this.overlayElement.remove();
    }

    updateElement(
        deltaState: OverlayState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.overlayElement
        );
    }
}
