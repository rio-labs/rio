import {
    componentsById,
    recursivelyDeleteComponent,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import { markEventAsHandled } from "../eventHandling";
import { PopupManager, positionFullscreen } from "../popupManager";
import { callRemoteMethodDiscardResponse } from "../rpc";
import { commitCss } from "../utils";
import { ComponentBase, ComponentState } from "./componentBase";

export type DialogContainerState = ComponentState & {
    _type_: "DialogContainer-builtin";
    content?: ComponentId;
    owning_component_id?: ComponentId;
    is_modal?: boolean;
    is_user_closable?: boolean;
};

export class DialogContainerComponent extends ComponentBase {
    declare state: Required<DialogContainerState>;

    private contentContainer: HTMLElement;

    // Dialogs are displayed via a popup manager. While this isn't strictly
    // necessary, this allows sharing the code for whether the dialog is modal,
    // user-closable and general styling.
    private popupManager: PopupManager;

    createElement(): HTMLElement {
        // Create the HTML elements
        let element = document.createElement("div");
        element.classList.add("rio-dialog-container");

        this.contentContainer = document.createElement("div");

        // Set up the popup manager
        this.popupManager = new PopupManager(
            element,
            this.contentContainer,
            positionFullscreen
        );

        return element;
    }

    onDestruction(): void {
        // Chain up
        super.onDestruction();

        // Rather than disappearing immediately, the dialog container would like
        // to fade out its content. This doesn't work though, because the
        // content is also deleted when the dialog container is. So create a
        // copy of the container's HTML and animate that instead.
        let phony = this.element.cloneNode(true) as HTMLElement;
        phony.style.pointerEvents = "none";

        phony.querySelectorAll("*").forEach((child) => {
            (child as HTMLElement).style.pointerEvents = "none";
        });

        document.body.appendChild(phony);
        commitCss(phony);

        // Animate the element
        phony.classList.remove("rio-dialog-container-enter");

        // Remove the element after the animation is done
        setTimeout(
            () => {
                phony.remove();
            },
            600 // Make sure this matches the CSS transition duration!
        );
    }

    updateElement(
        deltaState: DialogContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Content
        this.replaceOnlyChild(latentComponents, deltaState.content);

        // Modal
        if (deltaState.is_modal) {
            this.element.style.pointerEvents = "auto";
            this.element.style.removeProperty("background-color");
        } else {
            this.element.style.pointerEvents = "none";
            this.element.style.backgroundColor = "transparent";
        }

        // Owning component
        if (deltaState.owning_component_id !== undefined) {
            let owningComponent =
                componentsById[deltaState.owning_component_id]!;

            owningComponent.registerChild(latentComponents, this);
        }
    }
}
