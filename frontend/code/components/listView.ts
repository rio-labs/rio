import { componentsByElement, componentsById } from "../componentManagement";
import { ComponentId } from "../dataModels";
import {
    ComponentBase,
    ComponentState,
    DeltaState,
    Key,
} from "./componentBase";
import { CustomListItemComponent } from "./customListItem";
import { HeadingListItemComponent } from "./headingListItem";
import { SeparatorListItemComponent } from "./separatorListItem";

export type ListViewState = ComponentState & {
    _type_: "ListView-builtin";
    children: ComponentId[];
    selection_mode: "none" | "single" | "multiple";
    selected_items: Key[];
};

export class ListViewComponent extends ComponentBase<ListViewState> {
    private clickHandlers: Map<
        Key,
        [(event: MouseEvent) => void, ComponentId]
    > = new Map();
    private selectionKeysByOwner: Map<ComponentId, Set<Key>> = new Map();

    createElement(): HTMLElement {
        const element = document.createElement("div");
        element.classList.add("rio-list-view");
        element.classList.add("rio-selection-owner");
        return element;
    }

    updateElement(
        deltaState: DeltaState<ListViewState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Columns don't wrap their children in divs, but ListView does. Hence
        // the overridden updateElement.
        let needSelectionUpdate = false;
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
            needSelectionUpdate = true;
        }

        if (deltaState.selection_mode !== undefined) {
            this.state.selection_mode = deltaState.selection_mode;
            this.updateSelectionInteractivity();
            this.element.classList.toggle(
                "selectable",
                this.state.selection_mode !== "none"
            );
        }
        if (deltaState.selected_items !== undefined) {
            this.state.selected_items = deltaState.selected_items;
            this.updateSelectionStyles();
        }

        if (needSelectionUpdate) {
            Promise.resolve().then(() => {
                // a micro-task to make sure children are fully rendered
                this.updateSelectionInteractivity();
                this.updateSelectionStyles();
            });
        }
    }
    onChildGrowChanged(): void {
        this._updateChildStyles();
        this.updateSelectionStyles();

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
        let groupedChildren = new Set<HTMLElement>();
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
                curChild.previousElementSibling as HTMLElement
            );
            let nextIsGrouped = groupedChildren.has(
                curChild.nextElementSibling as HTMLElement
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

    /// Returns iterator over all child elements that have a key, along with the key
    private *_childrenWithKeys(
        element: Element | null = null
    ): IterableIterator<[HTMLElement, Key]> {
        const seenKeys = new Set<Key>();
        element = element ?? this.element;

        for (let child of element.querySelectorAll(
            ".rio-selectable-candidate"
        )) {
            let itemKey = keyForSelectable(child);
            if (itemKey !== null && !seenKeys.has(itemKey)) {
                seenKeys.add(itemKey);
                yield [child as HTMLElement, itemKey];
            }
        }
    }

    updateSelectionInteractivity(element: Element | null = null): void {
        element = element ?? this.element;
        for (let child of element.querySelectorAll(".rio-selection-owner")) {
            this.updateSelectionInteractivity(child);
        }
        const component = componentsByElement.get(element as HTMLElement);
        if (component !== undefined) {
            this._updateSelectionInteractivity(component);
        }
    }

    _updateSelectionInteractivity(component: ComponentBase): void {
        const newOwnedItems = new Set<[Element, Key]>();
        const componentId = component.id;
        const oldOwnedKeys =
            this.selectionKeysByOwner.get(componentId) ?? new Set<Key>();
        if (!this.selectionKeysByOwner.has(componentId)) {
            this.selectionKeysByOwner.set(componentId, oldOwnedKeys);
        }
        for (let [item, itemKey] of this._childrenWithKeys(component.element)) {
            // Claims new items by defaulting owner to componentId if not in clickHandlers
            const [oldHandler, ownerComponentId] = this.clickHandlers.get(
                itemKey
            ) ?? [null, componentId];
            const ownerComponentExists =
                componentsById[ownerComponentId] !== undefined;
            if (!ownerComponentExists) {
                const ownedKeys =
                    this.selectionKeysByOwner.get(ownerComponentId);
                for (const key of ownedKeys) {
                    oldOwnedKeys.add(key);
                }
                ownedKeys.clear();
                this.selectionKeysByOwner.delete(ownerComponentId);
            }
            if (ownerComponentId === componentId || !ownerComponentExists) {
                if (oldHandler) {
                    item.classList.remove("rio-selectable-item");
                    item.removeEventListener("click", oldHandler);
                }
                newOwnedItems.add([item, itemKey]);
            }
        }
        if (this.clickHandlers.size > 0) {
            for (const key of oldOwnedKeys) {
                this.clickHandlers.delete(key);
            }
            oldOwnedKeys.clear();
        }

        if (this.state.selection_mode !== "none") {
            for (let [item, itemKey] of newOwnedItems) {
                const handler = (event: MouseEvent) =>
                    this._handleItemClick(event, item, itemKey);
                item.addEventListener("click", handler);
                item.classList.add("rio-selectable-item");
                this.clickHandlers.set(itemKey, [handler, componentId]);
                oldOwnedKeys.add(itemKey);
            }
        }
    }

    _handleItemClick(event: MouseEvent, item: Element, itemKey: Key): void {
        if (this.state.selection_mode === "none") return;

        const currentSelection = [...this.state.selected_items];
        const isSelected = currentSelection.includes(itemKey);
        const ctrlKey = event.ctrlKey || event.metaKey;

        if (this.state.selection_mode === "single" || !ctrlKey) {
            this.state.selected_items = isSelected ? [] : [itemKey];
            this.updateSelectionStyles();
        } else if (this.state.selection_mode === "multiple") {
            if (isSelected) {
                this.state.selected_items = currentSelection.filter(
                    (key) => key !== itemKey
                );
            } else {
                this.state.selected_items = [...currentSelection, itemKey];
            }
            this._updateSelectionStyle(item, itemKey);
        }

        this._notifySelectionChange();
    }

    _updateSelectionStyle(item: Element, itemKey: Key) {
        item.classList.toggle(
            "selected",
            this.state.selected_items.includes(itemKey)
        );
    }

    updateSelectionStyles(element: Element | null = null): void {
        for (let [item, itemKey] of this._childrenWithKeys(element)) {
            this._updateSelectionStyle(item, itemKey);
        }
    }

    _notifySelectionChange(): void {
        // Send selection change to the backend
        this.sendMessageToBackend({
            type: "selectionChange",
            selected_items: this.state.selected_items,
        });
    }
}

function keyForSelectable(item: Element): Key | null {
    let currentElement: Element | null = item;
    while (currentElement !== null) {
        const component = componentsByElement.get(
            currentElement as HTMLElement
        );
        const key = component?.state.key ?? null;
        if (key !== null && key !== "") {
            return key;
        }
        currentElement = currentElement.parentElement;
    }
    console.warn("keyForSelectable: No key found in hierarchy for item", item);
    return null;
}
