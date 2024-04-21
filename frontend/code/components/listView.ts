import { componentsByElement } from '../componentManagement';
import { ComponentId } from '../dataModels';
import { ComponentBase } from './componentBase';
import { CustomListItemComponent } from './customListItem';
import { HeadingListItemComponent } from './headingListItem';
import { ColumnComponent, LinearContainerState } from './linearContainers';
import { SeparatorListItemComponent } from './separatorListItem';

export class ListViewComponent extends ColumnComponent {
    constructor(id: ComponentId, state: Required<LinearContainerState>) {
        state.spacing = 0;
        state.proportions = null;
        super(id, state);
    }

    createElement(): HTMLElement {
        let element = super.createElement();
        element.classList.add('rio-list-view');
        return element;
    }

    updateElement(
        deltaState: LinearContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Columns don't wrap their children in divs, but ListView does. Hence
        // the overridden updateElement.
        this.replaceChildren(
            latentComponents,
            deltaState.children,
            this.childContainer,
            true
        );

        // Clear everybody's position
        for (let child of this.childContainer.children) {
            let element = child.firstElementChild as HTMLElement;
            element.style.left = '0';
            element.style.top = '0';
        }

        // Update the styles of the children
        this._updateChildStyles();

        // Update the layout
        this.makeLayoutDirty();
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
        for (let child of this.childContainer.children) {
            let castChild = child as HTMLElement;

            if (this._isGroupedListItem(castChild)) {
                groupedChildren.add(castChild);
                castChild.classList.add('rio-listview-grouped');
            } else {
                castChild.classList.remove('rio-listview-grouped');
            }
        }

        // Round the corners of each first & last child in a a group, and add
        // separators between them.
        //
        // Make sure to work on a copy because the element will be modified by
        // the loop.
        for (let curChildUncast of Array.from(this.childContainer.children)) {
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
                ? '0'
                : 'var(--rio-global-corner-radius-medium)';
            let bottomRadius = nextIsGrouped
                ? '0'
                : 'var(--rio-global-corner-radius-medium)';

            curChild.style.borderTopLeftRadius = topRadius;
            curChild.style.borderTopRightRadius = topRadius;
            curChild.style.borderBottomLeftRadius = bottomRadius;
            curChild.style.borderBottomRightRadius = bottomRadius;

            curChild.style.overflow = 'hidden';
        }
    }
}
