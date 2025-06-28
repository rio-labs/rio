import { RippleEffect } from "../rippleEffect";
import { ComponentState, DeltaState } from "./componentBase";
import { ComponentId } from "../dataModels";
import {
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import { SelectableListItemComponent } from "./listItems";
import { PressableElement } from "../elements/pressableElement";

export type CustomTreeItemState = ComponentState & {
    _type_: "CustomTreeItem-builtin";
    content: ComponentId;
    is_expanded: boolean;
    pressable: boolean;
    children: ComponentId[];
    expand_button_open: ComponentId;
    expand_button_closed: ComponentId;
    expand_button_disabled: ComponentId;
};

export class CustomTreeItemComponent extends SelectableListItemComponent<CustomTreeItemState> {
    // If this item has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;
    private headerElement: HTMLElement;
    private expandButtonContainer: PressableElement;
    private contentContainerElement: HTMLElement;
    private childrenContainerElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-custom-tree-item");

        this.headerElement = this.pressToSelectButton = new PressableElement();
        this.headerElement.classList.add("rio-tree-header-row");
        element.appendChild(this.headerElement);

        this.expandButtonContainer = new PressableElement();
        this.expandButtonContainer.classList.add(
            "rio-tree-expand-button-container"
        );
        this.headerElement.appendChild(this.expandButtonContainer);

        this.contentContainerElement = document.createElement("div");
        this.contentContainerElement.classList.add(
            "rio-tree-content-container"
        );
        this.headerElement.appendChild(this.contentContainerElement);

        this.childrenContainerElement = document.createElement("div");
        this.childrenContainerElement.classList.add(
            "rio-tree-children-container"
        );
        element.appendChild(this.childrenContainerElement);

        return element;
    }

    updateElement(
        deltaState: DeltaState<CustomTreeItemState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.content !== undefined) {
            this.replaceOnlyChild(
                context,
                deltaState.content,
                this.contentContainerElement
            );
        }

        // Style the surface depending on whether it is pressable
        if (deltaState.pressable === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(
                    this.contentContainerElement
                );

                this.contentContainerElement.style.cursor = "pointer";
                this.contentContainerElement.style.setProperty(
                    "--hover-color",
                    "var(--rio-local-bg-active)"
                );

                this.contentContainerElement.onclick = this._onPress.bind(this);
            }
        } else if (deltaState.pressable === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;

                this.contentContainerElement.style.removeProperty("cursor");
                this.contentContainerElement.style.setProperty(
                    "--hover-color",
                    "transparent"
                );
                this.contentContainerElement.onclick = null;
            }
        }

        // update expansion style
        if (deltaState.is_expanded !== undefined) {
            this.state.is_expanded = deltaState.is_expanded;
            this._applyExpansionStyle();
        }

        // update children
        if (deltaState.children !== undefined) {
            this.replaceChildren(
                context,
                deltaState.children,
                this.childrenContainerElement
            );

            if (deltaState.children.length > 0) {
                this.expandButtonContainer.onPress =
                    this._toggleExpansion.bind(this);
            } else {
                this.expandButtonContainer.onPress = null;
            }
        }

        if (
            deltaState.is_expanded !== undefined ||
            deltaState.children != undefined
        ) {
            let hasChildren =
                (deltaState.children ?? this.state.children).length > 0;

            this._updateExpandButtonElement(hasChildren);
        }
    }

    private _updateExpandButtonElement(hasChildren: boolean) {
        const expandButtonComponentId = hasChildren
            ? this.state.is_expanded
                ? this.state.expand_button_open
                : this.state.expand_button_closed
            : this.state.expand_button_disabled;

        this.expandButtonContainer.innerHTML = "";
        this.expandButtonContainer.appendChild(
            componentsById[expandButtonComponentId].element
        );
    }

    private _onPress(): void {
        this.sendMessageToBackend({
            type: "press",
        });
    }

    private _applyExpansionStyle(): void {
        this.childrenContainerElement.style.display = this.state.is_expanded
            ? "block"
            : "none";
    }

    private _toggleExpansion(event: MouseEvent): void {
        const ctrlKey = event.ctrlKey || event.metaKey;

        if (!ctrlKey) {
            this.state.is_expanded = !this.state.is_expanded;

            this._applyExpansionStyle();
            this._updateExpandButtonElement(true);
            this.sendMessageToBackend({
                type: "toggleExpansion",
                is_expanded: this.state.is_expanded,
            });
        }
    }
}
