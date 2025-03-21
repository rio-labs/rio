import { ComponentId } from "../dataModels";
import { FullscreenPositioner, PopupManager } from "../popupManager";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type OverlayState = ComponentState & {
    _type_: "Overlay-builtin";
    content: ComponentId;
};

export class OverlayComponent extends ComponentBase<OverlayState> {
    private overlayContentElement: HTMLElement;
    private popupManager: PopupManager;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-overlay");

        this.overlayContentElement = document.createElement("div");
        this.overlayContentElement.classList.add("rio-overlay-content");
        this.overlayContentElement.dataset.ownerId = `${this.id}`;

        this.popupManager = new PopupManager({
            anchor: element,
            content: this.overlayContentElement,
            positioner: new FullscreenPositioner(),
            modal: false,
            userClosable: false,
        });

        requestAnimationFrame(() => {
            this.popupManager.isOpen = true;
        });

        return element;
    }

    onDestruction(): void {
        super.onDestruction();
        this.popupManager.destroy();
    }

    updateElement(
        deltaState: DeltaState<OverlayState>,
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
