import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { getPositionerByName, PopupManager } from "../popupManager";

export type TooltipState = ComponentState & {
    _type_: "Tooltip-builtin";
    anchor: ComponentId;
    _tip_component: ComponentId | null;
    position: "auto" | "left" | "top" | "right" | "bottom";
    gap: number;
};

export class TooltipComponent extends ComponentBase<TooltipState> {
    private popupElement: HTMLElement;
    private popupManager: PopupManager;

    createElement(): HTMLElement {
        // Set up the HTML
        let element = document.createElement("div");
        element.classList.add("rio-tooltip");

        this.popupElement = document.createElement("div");
        this.popupElement.classList.add(
            "rio-tooltip-popup",
            "rio-popup-manager-animation-scale",
            "rio-switcheroo-hud"
        );

        // Listen for events
        element.addEventListener("pointerenter", () => {
            this.popupManager.isOpen = true;
        });

        element.addEventListener("pointerleave", () => {
            this.popupManager.isOpen = false;
        });

        // Initialize the popup manager. Many of these values will be
        // overwritten by the updateElement method.
        this.popupManager = new PopupManager({
            anchor: element,
            content: this.popupElement,
            positioner: getPositionerByName("center", 0.0, 0.0),
            modal: false,
            userClosable: false,
        });

        return element;
    }

    updateElement(
        deltaState: DeltaState<TooltipState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the anchor
        if (deltaState.anchor !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.anchor,
                this.element
            );
        }

        // Update tip
        if (deltaState._tip_component !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState._tip_component,
                this.popupElement
            );
        }

        // Update the popup manager
        if (deltaState.position !== undefined || deltaState.gap !== undefined) {
            this.popupManager.positioner = getPositionerByName(
                deltaState.position ?? this.state.position,
                deltaState.gap ?? this.state.gap,
                0.5
            );
        }
    }

    onDestruction(): void {
        super.onDestruction();
        this.popupManager.destroy();
    }
}
