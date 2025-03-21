import { componentsByElement, componentsById } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { CustomListItemComponent } from "./customListItem";
import { HeadingListItemComponent } from "./headingListItem";
import { SeparatorListItemComponent } from "./separatorListItem";

export type ListViewState = ComponentState & {
    _type_: "ListView-builtin";
    children: ComponentId[];
};

export class ListViewComponent extends ComponentBase<ListViewState> {
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
        }
    }

    onChildGrowChanged(): void {
        // Visually style children
        this._updateChildStyles();

        // Set the children's `flex-grow`
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
}
