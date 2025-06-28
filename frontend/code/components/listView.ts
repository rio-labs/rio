import {
    componentsByElement,
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import {
    ComponentBase,
    ComponentState,
    DeltaState,
    Key,
} from "./componentBase";
import { CustomTreeItemComponent } from "./customTreeItem";
import {
    SelectableListItemComponent,
    CustomListItemComponent,
    HeadingListItemComponent,
    SeparatorListItemComponent,
} from "./listItems";

export type ListViewState = ComponentState & {
    _type_: "ListView-builtin";
    children: ComponentId[];
    selection_mode: "none" | "single" | "multiple";
    selected_items: Key[];
};

export class ListViewComponent extends ComponentBase<ListViewState> {
    private items = new Set<SelectableListItemComponent<ComponentState>>();

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        const element = document.createElement("div");
        element.classList.add("rio-list-view");
        return element;
    }

    updateElement(
        deltaState: DeltaState<ListViewState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        let needSelectabilityUpdate = false;

        if (deltaState.children !== undefined) {
            this.replaceChildren(
                context,
                deltaState.children,
                this.element,
                true
            );

            // Update the styles of the children
            this.state.children = deltaState.children;
            this.onChildGrowChanged();

            this.updateIsSelected();
            needSelectabilityUpdate = true;
        }

        if (deltaState.selection_mode !== undefined) {
            this.element.classList.toggle(
                "can-have-selection",
                deltaState.selection_mode !== "none"
            );

            this.state.selection_mode = deltaState.selection_mode;
            needSelectabilityUpdate = true;
        }

        if (deltaState.selected_items !== undefined) {
            this.state.selected_items = deltaState.selected_items;
            this.updateIsSelected();
        }

        if (needSelectabilityUpdate) {
            this.updateIsSelectable();
        }
    }

    registerItem(item: SelectableListItemComponent<ComponentState>): void {
        this.items.add(item);
        this.updateItemIsSelected(item);
        this.updateItemIsSelectable(item);
    }

    unregisterItem(item: SelectableListItemComponent<ComponentState>): void {
        this.items.delete(item);

        let index = this.state.selected_items.findIndex(
            (key) => key === item.state.key
        );
        if (index !== -1) {
            this.state.selected_items.splice(index, 1);
            this.updateSelection(this.state.selected_items);
        }
    }

    onChildGrowChanged(): void {
        this.updateChildStyles();
        this.updateIsSelected();

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
            comp instanceof SeparatorListItemComponent ||
            comp instanceof CustomTreeItemComponent
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

    updateChildStyles(): void {
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

    updateIsSelectable(): void {
        for (let item of this.items) {
            this.updateItemIsSelectable(item);
        }
    }

    updateItemIsSelectable(
        item: SelectableListItemComponent<ComponentState>
    ): void {
        item.isSelectable =
            item instanceof SelectableListItemComponent &&
            item.state.key !== null &&
            this.state.selection_mode !== "none";
    }

    onItemPress(
        item: SelectableListItemComponent<ComponentState>,
        event: PointerEvent | KeyboardEvent
    ): void {
        if (this.state.selection_mode === "none") {
            return;
        }

        if (this.state.selection_mode === "single" || !event.ctrlKey) {
            for (let otherItem of this.items) {
                otherItem.isSelected = false;
            }

            if (this.state.selected_items.includes(item.state.key)) {
                this.state.selected_items = [];
                item.isSelected = false;
            } else {
                this.state.selected_items = [item.state.key];
                item.isSelected = true;
            }
        } else {
            if (this.state.selected_items.includes(item.state.key)) {
                this.state.selected_items = this.state.selected_items.filter(
                    (key) => key !== item.state.key
                );
                item.isSelected = false;
            } else {
                this.state.selected_items.push(item.state.key);
                item.isSelected = true;
            }
        }

        this.updateSelection(this.state.selected_items);
    }

    updateSelection(selectedItems: Key[]): void {
        this.state.selected_items = selectedItems;

        this.sendMessageToBackend({
            type: "selectionChange",
            selected_items: selectedItems,
        });
    }

    updateIsSelected(): void {
        for (let item of this.items) {
            this.updateItemIsSelected(item);
        }
    }

    updateItemIsSelected(item: SelectableListItemComponent<ComponentState>) {
        item.isSelected = this.state.selected_items.includes(item.state.key);
    }
}
