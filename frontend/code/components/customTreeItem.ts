import { RippleEffect } from "../rippleEffect";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentId } from "../dataModels";
import { componentsById } from "../componentManagement";

export type CustomTreeItemState = ComponentState & {
    _type_: "CustomTreeItem-builtin";
    expand_button: ComponentId | null;
    content: ComponentId;
    children_container: ComponentId | null;
    is_expanded: boolean;
    pressable: boolean;
};

export class CustomTreeItemComponent extends ComponentBase<CustomTreeItemState> {
    // If this item has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;

    createElement(): HTMLElement {
        const element = this._addElement("div", "rio-custom-tree-item", null);
        const header = this._addElement("div", "rio-tree-header-row", element);
        this._addElement("div", "rio-tree-expand-button", header);
        this._addElement("div", "rio-tree-content-container", header);
        this._addElement("div", "rio-tree-children", element);
        return element;
    }

    private _addElement(
        elementType: str,
        elementClass: str,
        parentElement: HTMLElement | null
    ): HTMLElement {
        const element = document.createElement(elementType);
        element.classList.add(elementClass);
        if (parentElement !== null) {
            parentElement.appendChild(element);
        }
        return element;
    }

    updateElement(
        deltaState: DeltaState<CustomTreeItemState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        //update content container
        const contentContainerElement = this.element.querySelector(
            ".rio-tree-content-container"
        ) as HTMLElement;
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content !== undefined
                ? deltaState.content
                : this.state.content,
            contentContainerElement
        );
        if (this.parent?.state?.key) {
            contentContainerElement.classList.add("rio-selectable-item");
        } else {
            contentContainerElement.classList.remove("rio-selectable-item");
        }

        // Style the surface depending on whether it is pressable
        if (deltaState.pressable === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(contentContainerElement);

                contentContainerElement.style.cursor = "pointer";
                contentContainerElement.style.setProperty(
                    "--hover-color",
                    "var(--rio-local-bg-active)"
                );

                contentContainerElement.onclick = this._on_press.bind(this);
            }
        } else if (deltaState.pressable === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;

                contentContainerElement.style.removeProperty("cursor");
                contentContainerElement.style.setProperty(
                    "--hover-color",
                    "transparent"
                );

                contentContainerElement.onclick = null;
            }
        }

        //update children
        const childrenComponent =
            deltaState.children_container !== undefined
                ? deltaState.children_container
                : this.state.children_container;
        const childrenContainerElement = this.element.querySelector(
            ".rio-tree-children"
        ) as HTMLElement;

        this.replaceOnlyChild(
            latentComponents,
            childrenComponent,
            childrenContainerElement
        );

        //update expand button
        const expandButtonElement = this.element.querySelector(
            ".rio-tree-expand-button"
        ) as HTMLElement;

        this.replaceOnlyChild(
            latentComponents,
            deltaState.expand_button !== undefined
                ? deltaState.expand_button
                : this.state.expand_button,
            expandButtonElement
        );

        if (childrenComponent !== null) {
            expandButtonElement.classList.add("rio-tree-expand-button");
            expandButtonElement.addEventListener(
                "click",
                this._toggleExpansion.bind(this)
            );
        } else {
            expandButtonElement.classList.add("rio-tree-expand-placeholder");
            expandButtonElement.removeEventListener(
                "click",
                this._toggleExpansion.bind(this)
            );
        }

        //update expansion style
        if (deltaState.is_expanded !== undefined) {
            this._applyExpansionStyle(deltaState.is_expanded);
        }
    }

    private _on_press(): void {
        this.sendMessageToBackend({
            type: "press",
        });
    }

    private _applyExpansionStyle(isExpanded: boolean): void {
        const childrenContainerElement = this.element.querySelector(
            ".rio-tree-children"
        ) as HTMLElement;
        childrenContainerElement.style.display = isExpanded ? "block" : "none";
    }

    private _toggleExpansion(): void {
        this.state.is_expanded = !this.state.is_expanded;
        this._applyExpansionStyle(this.state.is_expanded);

        const expandButtonElement =
            componentsById[this.state.expand_button].element;

        expandButtonElement.textContent = this.state.is_expanded ? "▼" : "▶";

        this.sendMessageToBackend({
            type: "toggleExpansion",
            is_expanded: this.state.is_expanded,
        });
    }
}
