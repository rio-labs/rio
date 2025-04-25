import {
    componentsById,
    ComponentStatesUpdateContext,
    recursivelyDeleteComponent,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import { PopupManager } from "../popupManager";
import { FullscreenPositioner } from "../popupPositioners";
import { callRemoteMethodDiscardResponse } from "../rpc";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type DialogContainerState = ComponentState & {
    _type_: "DialogContainer-builtin";
    content: ComponentId;
    owning_component_id: ComponentId;
    is_modal: boolean;
    is_user_closable: boolean;
};

export class DialogContainerComponent extends ComponentBase<DialogContainerState> {
    private contentContainer: HTMLElement;

    // Dialogs are displayed via a popup manager. While this isn't strictly
    // necessary, this allows sharing the code for whether the dialog is modal,
    // user-closable and general styling.
    private popupManager: PopupManager;

    // Used to restore the keyboard focus when the dialog is closed
    private previouslyFocusedElement: Element | null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the HTML elements
        let element = document.createElement("div");
        element.classList.add("rio-dialog-container");

        this.contentContainer = document.createElement("div");
        this.contentContainer.classList.add("rio-dialog-container-content");

        // Set up the popup manager
        this.popupManager = new PopupManager({
            anchor: element,
            content: this.contentContainer,
            positioner: new FullscreenPositioner(),
            modal: true,
            userClosable: true,
            dialog: true,
            onUserClose: this.onUserClose.bind(this),
        });

        // Open the popup manager once we're confident that all components have
        // been created
        context.addEventListener("all states updated", () => {
            this.previouslyFocusedElement = document.activeElement;
            this.popupManager.isOpen = true;
        });

        return element;
    }

    onDestruction(): void {
        // Chain up
        super.onDestruction();

        // Tell Python about it
        callRemoteMethodDiscardResponse("dialogClosed", {
            dialog_root_component_id: this.id,
        });

        // Rather than disappearing immediately, the dialog container would like
        // to fade out its content. This doesn't work though, because the
        // content is also deleted when the dialog container is. So create a
        // copy of the container's HTML and animate that instead.
        //
        // Create the copy
        let contentRootElement = this.contentContainer.firstElementChild!;
        let phony = contentRootElement.cloneNode(true) as HTMLElement;

        // Make sure it doesn't interfere with user inputs
        phony.style.pointerEvents = "none";

        phony.querySelectorAll("*").forEach((child) => {
            (child as HTMLElement).style.pointerEvents = "none";
        });

        // Replace the content with the phony element
        contentRootElement.remove();
        this.contentContainer.appendChild(phony);

        // Close the popup manager, thus starting the outgoing animation
        this.popupManager.isOpen = false;

        // Clean up after the animation is done
        setTimeout(
            () => {
                this.popupManager.destroy();
            },
            // Make sure this matches or exceeds the CSS transition duration!
            600
        );

        // Restore the keyboard focus
        if (this.previouslyFocusedElement instanceof HTMLElement) {
            this.previouslyFocusedElement.focus();
        }
    }

    updateElement(
        deltaState: DeltaState<DialogContainerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Content
        this.replaceOnlyChild(
            context,
            deltaState.content,
            this.contentContainer
        );

        // Modal
        if (deltaState.is_modal !== undefined) {
            this.popupManager.modal = deltaState.is_modal;
        }

        // User closable
        if (deltaState.is_user_closable !== undefined) {
            this.popupManager.userClosable = deltaState.is_user_closable;
        }

        // Owning component
        if (deltaState.owning_component_id !== undefined) {
            let owningComponent =
                componentsById[deltaState.owning_component_id]!;

            owningComponent.registerChild(context, this);
        }
    }

    private onUserClose(): void {
        // Destroy the dialog container. This will trigger the destruction
        // function above, thus informing Python and properly cleaning up.
        recursivelyDeleteComponent(this);
    }
}
