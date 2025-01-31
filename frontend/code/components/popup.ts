import { applySwitcheroo } from "../designApplication";
import { ColorSet, ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";
import {
    DesktopDropdownPositioner,
    getPositionerByName,
    PopupManager,
} from "../popupManager";
import { stopPropagation } from "../eventHandling";

export type PopupState = ComponentState & {
    _type_: "Popup-builtin";
    anchor?: ComponentId;
    content?: ComponentId;
    is_open?: boolean;
    modal: boolean;
    user_closable: boolean;
    color?: ColorSet | "none";
    corner_radius?: number | [number, number, number, number];
    position?:
        | "auto"
        | "left"
        | "top"
        | "right"
        | "bottom"
        | "center"
        | "fullscreen"
        | "dropdown";
    alignment?: number;
    gap?: number;
};

export class PopupComponent extends ComponentBase {
    declare state: Required<PopupState>;

    private contentContainer: HTMLElement;

    private popupManager: PopupManager;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-popup-anchor");

        this.contentContainer = document.createElement("div");
        this.contentContainer.classList.add("rio-popup-content");

        // Initialize the popup manager. Many of these values will be
        // overwritten by the updateElement method.
        this.popupManager = new PopupManager({
            anchor: element,
            content: this.contentContainer,
            positioner: getPositionerByName("center", 0, 0.5),
            modal: false,
            userClosable: false,
            onUserClose: this.onUserClose.bind(this),
        });

        // Prevent clicking through the popup
        ["click", "pointerdown", "pointerup", "pointermove"].forEach(
            (eventType) => {
                this.contentContainer.addEventListener(
                    eventType,
                    stopPropagation
                );
            }
        );

        return element;
    }

    updateElement(
        deltaState: PopupState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the children
        if (deltaState.anchor !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.anchor,
                this.element
            );
        }

        if (deltaState.content !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.content,
                this.contentContainer
            );
        }

        // Update the popup manager
        if (
            deltaState.position !== undefined ||
            deltaState.alignment !== undefined ||
            deltaState.gap !== undefined
        ) {
            let position = deltaState.position ?? this.state.position;

            // Dropdowns on mobile have the problem that they want to be modal.
            // The logic for setting `modal` and `user_closable` becomes a mess.
            // So for now, we always use desktop mode for dropdowns.
            if (position === "dropdown") {
                this.popupManager.positioner = new DesktopDropdownPositioner();
            } else {
                this.popupManager.positioner = getPositionerByName(
                    position,
                    deltaState.gap ?? this.state.gap,
                    deltaState.alignment ?? this.state.alignment
                );
            }

            this.popupManager.userClosable =
                deltaState.user_closable ?? this.state.user_closable;
        }

        // Open / Close
        if (deltaState.is_open !== undefined) {
            // If the Popup was *created* with `is_open=True`, then our element
            // isn't attached to the DOM yet and trying to open the popup will
            // fail. Lazy workaround: Delay it.
            requestAnimationFrame(() => {
                this.popupManager.isOpen = deltaState.is_open!;
            });
        }

        // Colorize
        if (deltaState.color === "none") {
            applySwitcheroo(this.contentContainer, "keep");
            this.contentContainer.style.removeProperty("background-color");
            this.contentContainer.style.removeProperty("box-shadow");
        } else if (deltaState.color !== undefined) {
            applySwitcheroo(this.contentContainer, deltaState.color);
            this.contentContainer.style.backgroundColor = `var(--rio-local-bg)`;
            this.contentContainer.style.boxShadow = `0 0 1rem var(--rio-global-shadow-color)`;
        }

        // Update the corner radius
        if (deltaState.corner_radius !== undefined) {
            if (typeof deltaState.corner_radius === "number") {
                this.contentContainer.style.borderRadius = `${deltaState.corner_radius}rem`;
            } else {
                this.contentContainer.style.borderRadius = `${deltaState.corner_radius[0]}rem ${deltaState.corner_radius[1]}rem ${deltaState.corner_radius[2]}rem ${deltaState.corner_radius[3]}rem`;
            }
        }

        // Modal
        if (deltaState.modal !== undefined) {
            this.popupManager.modal = deltaState.modal;
        }

        // User closable
        if (deltaState.user_closable !== undefined) {
            this.popupManager.userClosable = deltaState.user_closable;
        }
    }

    onDestruction(): void {
        super.onDestruction();
        this.popupManager.destroy();
    }

    onUserClose(): void {
        // The popup manager was closed by external user action. This doesn't
        // need any updates to the popup manager, but Python should be notified
        // of the state change.
        this.setStateAndNotifyBackend({
            is_open: false,
        });
    }
}
