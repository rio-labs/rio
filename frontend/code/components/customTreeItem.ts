import { RippleEffect } from "../rippleEffect";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentId } from "../dataModels";
import { componentsById } from "../componentManagement";
import { ListViewComponent } from "./listView";
import { replaceElement } from "../utils";

export type CustomTreeItemState = ComponentState & {
    _type_: "CustomTreeItem-builtin";
    content: ComponentId;
    is_expanded: boolean;
    pressable: boolean;
    children: ComponentId[];
    expand_button_open: ComponentId | null;
    expand_button_closed: ComponentId | null;
    expand_button_disabled: ComponentId | null;
};

export class CustomTreeItemComponent extends ComponentBase<CustomTreeItemState> {
    // If this item has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;
    private owningView: ListViewComponent | null = null;
    private headerElement: HTMLElement;
    private expandButtonElement: HTMLElement;
    private contentContainerElement: HTMLElement;
    private childrenContainerElement: HTMLElement;
    private expandButtonHandler: (event: MouseEvent) => void;

    createElement(): HTMLElement {
        const element = this._addElement("div", "rio-custom-tree-item", null);
        const header = this._addElement("div", "rio-tree-header-row", element);
        this.headerElement = header;
        this.expandButtonElement = this._addElement(
            "div",
            "rio-tree-expand-button",
            header
        );
        this.contentContainerElement = this._addElement(
            "div",
            "rio-tree-content-container",
            header
        );
        this.contentContainerElement.classList.add("rio-selectable-candidate");
        this.childrenContainerElement = this._addElement(
            "div",
            "rio-tree-children",
            element
        );
        this.expandButtonHandler = this._toggleExpansion.bind(this);
        element.classList.add("rio-selection-owner");
        return element;
    }

    private _addElement(
        elementType: string,
        elementClass: string,
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

        if (deltaState.content !== undefined) {
            //update content container
            this.replaceOnlyChild(
                latentComponents,
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

                this.contentContainerElement.onclick =
                    this._on_press.bind(this);
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

        //update expansion style
        if (deltaState.is_expanded !== undefined) {
            this.state.is_expanded = deltaState.is_expanded;
            this._applyExpansionStyle();
        }

        //update children
        if (deltaState.children !== undefined) {
            this.replaceChildren(
                latentComponents,
                deltaState.children,
                this.childrenContainerElement
            );
            this.headerElement.removeEventListener(
                "click",
                this.expandButtonHandler
            );
            if (deltaState.children.length > 0) {
                this.headerElement.addEventListener(
                    "click",
                    this.expandButtonHandler
                );
            }
            Promise.resolve().then(() => {
                // a micro-task to make sure children are fully rendered
                const owningView = this._getOwningView();
                owningView.updateSelectionInteractivity(this.element);
                owningView.updateSelectionStyles(this.element);
            });
            this.state.children = deltaState.children;
        }

        if (
            deltaState.is_expanded !== undefined ||
            deltaState.children != undefined
        ) {
            const hasChildren =
                this.state.children !== undefined &&
                this.state.children.length > 0;
            this.expandButtonElement.classList.toggle(
                "rio-tree-expand-button",
                hasChildren
            );
            this.expandButtonElement.classList.toggle(
                "rio-tree-expand-placeholder",
                !hasChildren
            );

            this._updateExpandButtonElement(hasChildren);
        }
    }

    private _updateExpandButtonElement(hasChildren) {
        const expandButtonComponentId = hasChildren
            ? this.state.is_expanded
                ? this.state.expand_button_open
                : this.state.expand_button_closed
            : this.state.expand_button_disabled;
        this.expandButtonElement.innerHTML = "";
        this.expandButtonElement.appendChild(
            componentsById[expandButtonComponentId].element
        );
    }

    private _getOwningView(): ListViewComponent | null {
        if (this.owningView === null) {
            let currentComponent: ComponentBase | null = this;
            while (currentComponent) {
                if (currentComponent instanceof ListViewComponent) {
                    this.owningView = currentComponent;
                    break;
                }
                currentComponent = currentComponent.parent;
            }
        }
        return this.owningView;
    }

    private _on_press(): void {
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
