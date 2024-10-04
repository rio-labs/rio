import { recursivelyDeleteComponent } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { markEventAsHandled } from "../eventHandling";
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

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement("div");
        element.classList.add("rio-dialog-container", "rio-switcheroo-neutral");

        // Since dialog containers aren't part of the component tree, they're
        // themselves responsible for adding themselves to the DOM.
        document.body.appendChild(element);

        // Animate the element
        requestAnimationFrame(() => {
            commitCss(element);
            element.classList.add("rio-dialog-container-enter");
        });

        // Listen for outside clicks
        element.addEventListener("click", (event) => {
            markEventAsHandled(event);

            // Don't close the dialog if the click was inside the dialog. This
            // is a bit tricky, because of various cases:
            //
            // - The click was handled by a component inside of the dialog (e.g.
            //   a Button). This is simple, since the event will never reach the
            //   dialog container.
            // - The click was onto a component in the dialog, but not handled.
            //   (Think a `rio.Card`). This must be detected and the dialog NOT
            //   closed.
            // - The click was technically into a component, but that component
            //   doesn't accept clicks. (Think the spacing of a `rio.Row`.)
            //   Since no component was technically clicked, the dialog should
            //   close.
            if (event.target !== element) {
                return;
            }

            // Is the dialog user-closable?
            if (!this.state.is_user_closable) {
                return;
            }

            // Yes! Close it. First, inform the server.
            callRemoteMethodDiscardResponse("dialogClosed", {
                dialogRootComponentId: this.id,
            });

            // Clean up
            recursivelyDeleteComponent(this);
        });

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
    }
}
