import { ComponentBase, ComponentState } from './componentBase';
import { LayoutContext } from '../layouting';
import { componentsById } from '../componentManagement';
import { pixelsPerRem } from '../app';

export type LayoutDisplayState = ComponentState & {
    _type_: 'LayoutDisplay-builtin';
    component_id: number;
};

function shouldDisplayComponent(comp: ComponentBase): boolean {
    return !comp.state._rio_internal_;
}

function _drillDown(comp: ComponentBase): ComponentBase[] {
    // Is this component displayable?
    if (shouldDisplayComponent(comp)) {
        return [comp];
    }

    // No, drill down
    let result: ComponentBase[] = [];

    for (let child of comp.children) {
        result.push(..._drillDown(child));
    }

    return result;
}

/// Given a component, return all of its children which should be displayed
/// in the tree.
function getDisplayableChildren(comp: ComponentBase): ComponentBase[] {
    let result: ComponentBase[] = [];

    // Keep drilling down until a component which should be displayed
    // is encountered
    for (let child of comp.children) {
        result.push(..._drillDown(child));
    }

    return result;
}

export class LayoutDisplayComponent extends ComponentBase {
    state: Required<LayoutDisplayState>;

    // Represents the target component's parent. It matches the aspect ratio of
    // the parent and is centered within this component.
    parentElement: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-layout-display');

        this.parentElement = document.createElement('div');
        this.parentElement.classList.add('rio-layout-display-parent');
        element.appendChild(this.parentElement);

        return element;
    }

    updateElement(
        deltaState: LayoutDisplayState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Has the target component changed?
        if (deltaState.component_id !== undefined) {
            // Trigger a re-layout
            this.makeLayoutDirty();
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // This component doesn't particularly care about its size. However, it
        // would be nice to have the correct aspect ratio.
        //
        // It's probably not remotely legal to access the natural width of
        // another component during layouting, but what the heck. This doesn't
        // do anything other than _attempting_ to get the correct aspect ratio.
        // Without this we're guaranteed to get a wrong one.
        let targetComponent: ComponentBase =
            componentsById[this.state.component_id]!;
        let parentComponent = targetComponent.getParentExcludingInjected();

        if (parentComponent === null || parentComponent.allocatedWidth === 0) {
            this.naturalHeight = 0;
        } else {
            this.naturalHeight =
                (this.allocatedWidth * parentComponent.allocatedHeight) /
                parentComponent.allocatedWidth;
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Let the code below assume that we have a reasonable size
        if (this.allocatedWidth === 0 || this.allocatedHeight === 0) {
            return;
        }

        setTimeout(() => {
            this.updateContent();
        }, 0);
    }

    updateContent(): void {
        // Get a reference to the target component
        let targetComponent: ComponentBase =
            componentsById[this.state.component_id]!;

        // Look up the parent
        let parentComponent = targetComponent.getParentExcludingInjected();
        let parentLayout: number[];

        if (parentComponent === null) {
            parentLayout = [
                0,
                0,
                window.innerWidth / pixelsPerRem,
                window.innerHeight / pixelsPerRem,
            ];
        } else {
            let parentRect = parentComponent.element.getBoundingClientRect();
            parentLayout = [
                parentRect.left / pixelsPerRem,
                parentRect.top / pixelsPerRem,
                parentRect.width / pixelsPerRem,
                parentRect.height / pixelsPerRem,
            ];
        }
        let [
            parentLeftInViewport,
            parentTopInViewport,
            parentAllocatedWidth,
            parentAllocatedHeight,
        ] = parentLayout;

        // Find all siblings
        let children: ComponentBase[];

        if (parentComponent === null) {
            children = [targetComponent];
        } else {
            children = getDisplayableChildren(parentComponent);
        }

        // Decide on a scale. Display everything as large as possible, while
        // fitting it into the allocated space and without distorting the aspect
        // ratio.
        let scaleX = this.allocatedWidth / parentAllocatedWidth;
        let scaleY = this.allocatedHeight / parentAllocatedHeight;
        let scaleRem: number, scalePer: number;

        if (scaleX < scaleY) {
            scaleRem = scaleX;
            scalePer = (scaleX / this.allocatedWidth) * 100;
        } else {
            scaleRem = scaleY;
            scalePer = (scaleY / this.allocatedHeight) * 100;
        }

        // Resize the parent representation
        this.parentElement.style.width = `${parentAllocatedWidth * scaleRem}rem`;
        this.parentElement.style.height = `${parentAllocatedHeight * scaleRem}rem`;

        // Remove any previous content
        this.parentElement.innerHTML = '';

        // Add all children
        for (let childComponent of children) {
            // Create the HTML representation
            let childElement = document.createElement('div');
            childElement.classList.add('rio-layout-display-child');
            this.parentElement.appendChild(childElement);

            let marginElement = document.createElement('div');
            marginElement.classList.add('rio-layout-display-margin');
            this.parentElement.appendChild(marginElement);

            // Is this the selected component?
            if (childComponent.id === targetComponent.id) {
                childElement.classList.add('rio-layout-display-target');
            }

            // Label the child
            childElement.innerText = childComponent.state._python_type_;

            // Position the child
            let childRect = childComponent.element.getBoundingClientRect();

            let childLeft =
                childRect.left / pixelsPerRem - parentLeftInViewport;
            let childTop = childRect.top / pixelsPerRem - parentTopInViewport;

            childElement.style.left = `${childLeft * scalePer}%`;
            childElement.style.top = `${childTop * scalePer}%`;

            // Size the child
            childElement.style.width = `${
                childComponent.allocatedWidth * scalePer
            }%`;
            childElement.style.height = `${
                childComponent.allocatedHeight * scalePer
            }%`;

            console.debug('---');
            console.debug(
                childComponent.allocatedWidth,
                childComponent.allocatedHeight
            );
            console.debug(parentAllocatedWidth, parentAllocatedHeight);
            console.debug(scaleRem, scalePer);
            console.debug(
                childComponent.allocatedWidth * scalePer,
                childComponent.allocatedHeight * scalePer
            );

            // Position the margin
            let margins = childComponent.state._margin_;

            let marginLeft = childLeft - margins[0];
            let marginTop = childTop - margins[1];

            marginElement.style.left = `${marginLeft * scalePer}%`;
            marginElement.style.top = `${marginTop * scalePer}%`;

            // Size the margin
            marginElement.style.width = `${
                (childComponent.allocatedWidth + margins[0] + margins[2]) *
                scalePer
            }%`;

            marginElement.style.height = `${
                (childComponent.allocatedHeight + margins[1] + margins[3]) *
                scalePer
            }%`;

            // Allow selecting the component
            childElement.onclick = () => {
                // Make sure the child id is a number, since this isn't
                // guaranteed in the frontend
                console.assert(typeof childComponent.id === 'number');

                console.log('Selected component', childComponent.id);

                // Update the state
                this.setStateAndNotifyBackend({
                    component_id: childComponent.id,
                });
            };
        }
    }
}
