import { componentsByElement, componentsById } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { CustomListItemComponent } from "./customListItem";
import { HeadingListItemComponent } from "./headingListItem";
import { SeparatorListItemComponent } from "./separatorListItem";

export type ListViewState = ComponentState & {
    _type_: "ListView-builtin";
    children: ComponentId[];
    selection_mode: "none" | "single" | "multiple"; // Selection mode
    selected_keys: (string | number)[]; // Indices of selected items
};

export class ListViewComponent extends ComponentBase<ListViewState> {
    private clickHandlers: Map<string | number, (event: MouseEvent) => void> =
        new Map();

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-list-view");
        return element;
    }

    updateElement(
        deltaState: DeltaState<ListViewState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Columns don't wrap their children in divs, but ListView does. Hence
        // the overridden updateElement.
        if (deltaState.children !== undefined) {
            this.replaceChildren(
                latentComponents,
                deltaState.children,
                this.element,
                true
            );

            // Update the styles of the children
            this.state.children = deltaState.children;
            this.onChildGrowChanged();
            this._updateSelectionInteractivity(); // Reapply handlers after children update
        }

        if (deltaState.selection_mode !== undefined) {
            this.state.selection_mode = deltaState.selection_mode;
            this._updateSelectionInteractivity();
        }
        if (deltaState.selected_keys !== undefined) {
            this.state.selected_keys = deltaState.selected_keys;
            this._updateSelectionStyles();
        }
    }

    onChildGrowChanged(): void {
        this._updateChildStyles();
        this._updateSelectionStyles();

        let hasGrowers = false;
        for (let [index, childId] of this.state.children.entries()) {
            let childComponent = componentsById[childId]!;
            let childWrapper = this.element.children[index] as HTMLElement;

            if (childComponent.state._grow_[1]) {
                hasGrowers = true;
                childWrapper.style.flexGrow = "1";
            } else {
                childWrapper.style.flexGrow = "0";
            }
        }

        // If nobody wants to grow, all of them do
        if (!hasGrowers) {
            for (let childWrapper of this.element.children) {
                (childWrapper as HTMLElement).style.flexGrow = "1";
            }
        }
    }

    _isGroupedListItemWorker(comp: ComponentBase): boolean {
        // Is this a recognized list item type?
        if (
            comp instanceof HeadingListItemComponent ||
            comp instanceof SeparatorListItemComponent
        ) {
            return false;
        }

        if (comp instanceof CustomListItemComponent) {
            return true;
        }

        // If the component only has a single child, drill down
        if (comp.children.size === 1) {
            return this._isGroupedListItemWorker(
                comp.children.values().next().value
            );
        }

        // Everything else defaults to being grouped
        return true;
    }

    _isGroupedListItem(elem: HTMLElement): boolean {
        let comp = componentsByElement.get(
            elem.firstElementChild as HTMLElement
        );

        if (comp === undefined) {
            throw new Error(`Cannot find component for list element ${elem}`);
        }

        return this._isGroupedListItemWorker(comp);
    }

    _updateChildStyles(): void {
        // Precompute which children are grouped
        let groupedChildren = new Set<any>();
        for (let child of this.element.children) {
            let castChild = child as HTMLElement;

            if (this._isGroupedListItem(castChild)) {
                groupedChildren.add(castChild);
                castChild.classList.add("rio-listview-grouped");
            } else {
                castChild.classList.remove("rio-listview-grouped");
            }
        }

        // Round the corners of each first & last child in a a group, and add
        // separators between them.
        //
        // Make sure to work on a copy because the element will be modified by
        // the loop.
        for (let curChildUncast of Array.from(this.element.children)) {
            let curChild = curChildUncast as HTMLElement;

            // Is this even a regular list item?
            let curIsGrouped = groupedChildren.has(curChild);

            // Look up the neighboring elements
            let prevIsGrouped = groupedChildren.has(
                curChild.previousElementSibling
            );
            let nextIsGrouped = groupedChildren.has(
                curChild.nextElementSibling
            );

            if (!curIsGrouped) {
                continue;
            }

            // Round the corners
            let topRadius = prevIsGrouped
                ? "0"
                : "var(--rio-global-corner-radius-medium)";
            let bottomRadius = nextIsGrouped
                ? "0"
                : "var(--rio-global-corner-radius-medium)";

            curChild.style.borderTopLeftRadius = topRadius;
            curChild.style.borderTopRightRadius = topRadius;
            curChild.style.borderBottomLeftRadius = bottomRadius;
            curChild.style.borderBottomRightRadius = bottomRadius;

            curChild.style.overflow = "hidden";
        }
    }

    private _itemKey(item: HTMLElement): string | number | null {
        const component = componentsByElement.get(
            item.firstElementChild as HTMLElement
        );
        const key = component?.state._key_ ?? null;
        if (key === null || key === "") {
            console.warn("No key found for item", item);
        }
        return key;
    }

    _updateSelectionInteractivity(): void {
        // Remove all existing listeners from current DOM elements
        if (this.clickHandlers.size > 0) {
            this.element
                .querySelectorAll(".rio-listview-grouped")
                .forEach((item) => {
                    const itemKey = this._itemKey(item);
                    if (!itemKey) return;

                    const oldHandler = this.clickHandlers.get(itemKey);
                    if (oldHandler) {
                        item.removeEventListener("click", oldHandler);
                    }
                });
            this.clickHandlers.clear(); // Clear all handlers when selection is disabled
        }

        if (this.state.selection_mode !== "none") {
            this.element.classList.add("selectable");
            this.element
                .querySelectorAll(".rio-listview-grouped")
                .forEach((item) => {
                    const itemKey = this._itemKey(item);
                    if (!itemKey) return;

                    // Create and store a new handler for this key
                    const handler = (event: MouseEvent) =>
                        this._handleItemClick(itemKey);
                    item.addEventListener("click", handler);
                    this.clickHandlers.set(itemKey, handler);
                });
        } else {
            this.element.classList.remove("selectable");
        }
    }

    _handleItemClick(itemKey: string | number): void {
        if (this.state.selection_mode === "none") return;

        const currentSelection = [...this.state.selected_keys];
        const isSelected = currentSelection.includes(itemKey);

        if (this.state.selection_mode === "single") {
            this.state.selected_keys = isSelected ? [] : [itemKey];
        } else if (this.state.selection_mode === "multiple") {
            if (isSelected) {
                this.state.selected_keys = currentSelection.filter(
                    (key) => key !== itemKey
                );
            } else {
                this.state.selected_keys = [...currentSelection, itemKey];
            }
        }

        this._updateSelectionStyles();
        this._notifySelectionChange();
    }

    _updateSelectionStyles(): void {
        this.element
            .querySelectorAll(".rio-listview-grouped")
            .forEach((item) => {
                const itemKey = this._itemKey(item);
                const listItem = item.querySelector(".rio-custom-list-item");
                if (listItem !== null && itemKey !== null) {
                    if (this.state.selected_keys.includes(itemKey)) {
                        listItem.classList.add("selected");
                    } else {
                        listItem.classList.remove("selected");
                    }
                }
            });
    }

    _notifySelectionChange(): void {
        // Send selection change to the backend
        this.sendMessageToBackend({
            type: "selectionChange",
            selected_keys: this.state.selected_keys,
        });
    }
}
