import { applySwitcheroo } from "../designApplication";
import { ColorSet, ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { PopupManager } from "../popupManager";
import { stopPropagation } from "../eventHandling";
import {
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import {
    DesktopDropdownPositioner,
    getPositionerByName,
} from "../popupPositioners";

export type PopupState = ComponentState & {
    _type_: "Popup-builtin";
    anchor: ComponentId;
    content: ComponentId;
    is_open: boolean;
    modal: boolean;
    user_closable: boolean;
    color: ColorSet | "none";
    corner_radius: number | [number, number, number, number];
    position:
        | "auto"
        | "left"
        | "top"
        | "right"
        | "bottom"
        | "center"
        | "fullscreen"
        | "dropdown";
    alignment: number;
    gap: number;
};

export class PopupComponent extends ComponentBase<PopupState> {
    private popupContentElement: HTMLElement;
    private popupScrollerElement: HTMLElement;

    private popupManager: PopupManager;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-popup-anchor");

        this.popupContentElement = document.createElement("div");
        this.popupContentElement.classList.add("rio-popup-content");

        this.popupScrollerElement = document.createElement("div");
        this.popupScrollerElement.classList.add("rio-popup-scroller");
        this.popupContentElement.appendChild(this.popupScrollerElement);

        // Instantiate a PopupManager with a dummy anchor for now. To ensure
        // correct interaction with alignment and margin, the popup manager must
        // use the child's `element` as its anchor, which we can only do later,
        // in `updateElement`.
        this.popupManager = new PopupManager({
            anchor: element,
            content: this.popupContentElement,
            positioner: getPositionerByName("center", 0, 0.5),
            modal: false,
            userClosable: false,
            onUserClose: this.onUserClose.bind(this),
        });

        // Prevent clicking through the popup
        ["click", "pointerdown", "pointerup", "pointermove"].forEach(
            (eventType) => {
                this.popupContentElement.addEventListener(
                    eventType,
                    stopPropagation
                );
            }
        );

        return element;
    }

    updateElement(
        deltaState: DeltaState<PopupState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the children
        if (deltaState.anchor !== undefined) {
            this.replaceOnlyChild(context, deltaState.anchor, this.element);

            // To ensure correct interaction with alignment and margin, the
            // popup manager must use the child's `element` as its anchor
            let child = componentsById[deltaState.anchor]!;
            this.popupManager.anchor = child.element;
        }

        if (deltaState.content !== undefined) {
            this.replaceOnlyChild(
                context,
                deltaState.content,
                this.popupScrollerElement
            );
        }

        // Update the popup manager
        if (
            deltaState.position !== undefined ||
            deltaState.alignment !== undefined ||
            deltaState.gap !== undefined
        ) {
            let position = deltaState.position ?? this.state.position;
            this.popupContentElement.dataset.position = position;

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
            this.popupManager.modal = deltaState.modal ?? this.state.modal;
        }

        // Open / Close
        if (deltaState.is_open !== undefined) {
            // If the Popup was *created* with `is_open=True`, then our element
            // isn't attached to the DOM yet and trying to open the popup will
            // fail. Lazy workaround: Delay it.
            //
            // FIXME: This is still a problem if you have a Popup inside of
            // another Popup.
            requestAnimationFrame(() => {
                this.popupManager.isOpen = deltaState.is_open!;
            });
        }

        // Colorize
        if (deltaState.color === "none") {
            applySwitcheroo(this.popupContentElement, "keep");
            this.popupContentElement.style.removeProperty("background-color");
            this.popupContentElement.style.removeProperty("box-shadow");
        } else if (deltaState.color !== undefined) {
            applySwitcheroo(this.popupContentElement, deltaState.color);
            this.popupContentElement.style.backgroundColor =
                "var(--rio-local-bg)";
            this.popupContentElement.style.boxShadow = `0 0 1rem var(--rio-global-shadow-color)`;
        }

        // Update the corner radius
        if (deltaState.corner_radius !== undefined) {
            if (typeof deltaState.corner_radius === "number") {
                this.popupContentElement.style.borderRadius = `${deltaState.corner_radius}rem`;
            } else {
                this.popupContentElement.style.borderRadius = `${deltaState.corner_radius[0]}rem ${deltaState.corner_radius[1]}rem ${deltaState.corner_radius[2]}rem ${deltaState.corner_radius[3]}rem`;
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
