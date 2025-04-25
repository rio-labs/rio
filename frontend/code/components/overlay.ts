import { ComponentStatesUpdateContext } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { PopupManager } from "../popupManager";
import { FullscreenPositioner } from "../popupPositioners";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type OverlayState = ComponentState & {
    _type_: "Overlay-builtin";
    content: ComponentId;
};

export class OverlayComponent extends ComponentBase<OverlayState> {
    private overlayContentElement: HTMLElement;
    private popupManager: PopupManager;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
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
            moveKeyboardFocusInside: false,
        });

        context.addEventListener("all states updated", () => {
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
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(
            context,
            deltaState.content,
            this.overlayContentElement
        );
    }
}
