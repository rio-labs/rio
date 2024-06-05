import { ComponentBase, ComponentState } from './componentBase';
import { LayoutContext } from '../layouting';
import { componentsById } from '../componentManagement';
import { pixelsPerRem } from '../app';
import { getDisplayableChildren } from '../devToolsTreeWalk';
import { Highlighter } from '../highlighter';
import { DevToolsConnectorComponent } from './devToolsConnector';
import { eventRateLimiter as rateLimit } from '../eventRateLimiter';

export type LayoutDisplayState = ComponentState & {
    _type_: 'LayoutDisplay-builtin';
    component_id?: number;
    max_requested_height?: number | null;
};

export class LayoutDisplayComponent extends ComponentBase {
    state: Required<LayoutDisplayState>;

    // Represents the target component's parent. It matches the aspect ratio of
    // the parent and is centered within this component.
    parentElement: HTMLElement;

    // Helper class for highlighting components
    highlighter: Highlighter;

    // Keep track of which element the user is currently hovering over
    parentIsHovered: boolean = false;
    hoveredChild: HTMLElement | null = null;

    rateLimitedNotifyBackendOfChange: () => void;

    createElement(): HTMLElement {
        // Register this component with the global dev tools component, so it
        // receives updates when a component's state changes.
        let devTools: DevToolsConnectorComponent = globalThis.RIO_DEV_TOOLS;
        console.assert(devTools !== null);
        devTools.componentIdsToLayoutDisplays.set(this.id, this);

        // Initialize the HTML
        let element = document.createElement('div');
        element.classList.add('rio-layout-display');

        this.parentElement = document.createElement('div');
        this.parentElement.classList.add('rio-layout-display-parent');
        element.appendChild(this.parentElement);

        // Create the highlighter
        this.highlighter = new Highlighter();

        // Listen to mouse events
        this.parentElement.onmouseenter = () => {
            this.parentIsHovered = true;
            this.updateHighlighter();
        };

        this.parentElement.onmouseleave = () => {
            this.parentIsHovered = false;
            this.updateHighlighter();
        };

        // Create a rate-limited version of the notifyBackendOfChange function
        this.rateLimitedNotifyBackendOfChange = rateLimit(
            this._notifyBackendOfChange.bind(this),
            300
        );

        return element;
    }

    onDestruction(): void {
        // Unregister this component from the global dev tools component
        let devTools: DevToolsConnectorComponent = globalThis.RIO_DEV_TOOLS;
        console.assert(devTools !== null);
        devTools.componentIdsToLayoutDisplays.delete(this.id);

        // Destroy the highlighter
        this.highlighter.destroy();
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

    _notifyBackendOfChange(): void {
        this.sendMessageToBackend({
            type: 'layoutChange',
        });
    }

    /// Called by the global dev tools connector when a re-layout was just
    /// performed.
    public afterLayoutUpdate(): void {
        // Update the content
        setTimeout(() => {
            this.updateContent();
        }, 0);

        // Tell the backend about it
        this.rateLimitedNotifyBackendOfChange();
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

        if (targetComponent === undefined) {
            this.naturalHeight = 0;
            return;
        }

        let parentComponent = targetComponent.getParentExcludingInjected();

        if (parentComponent === null || parentComponent.allocatedWidth === 0) {
            this.naturalHeight = 0;
        } else {
            this.naturalHeight =
                (this.allocatedWidth * parentComponent.allocatedHeight) /
                parentComponent.allocatedWidth;
        }

        // With all of that said, never request more than the max requested
        // height
        if (this.state.max_requested_height !== null) {
            this.naturalHeight = Math.min(
                this.naturalHeight,
                this.state.max_requested_height
            );
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Let the code below assume that we have a reasonable size
        if (this.allocatedWidth === 0 || this.allocatedHeight === 0) {
            return;
        }
    }

    updateContent(): void {
        // Remove any previous content
        this.parentElement.innerHTML = '';

        // Get a reference to the target component
        let targetComponent: ComponentBase =
            componentsById[this.state.component_id]!;

        if (targetComponent === undefined) {
            return;
        }

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
        let scaleRem: number = Math.min(
            this.allocatedWidth / parentAllocatedWidth,
            this.allocatedHeight / parentAllocatedHeight
        );

        let scalePerX = 100 / parentAllocatedWidth;
        let scalePerY = 100 / parentAllocatedHeight;

        // Resize the parent representation
        this.parentElement.style.width = `${
            parentAllocatedWidth * scaleRem
        }rem`;
        this.parentElement.style.height = `${
            parentAllocatedHeight * scaleRem
        }rem`;

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
            let isTarget = childComponent.id === targetComponent.id;
            if (isTarget) {
                childElement.classList.add('rio-layout-display-target');
            }

            // Label the child
            childElement.innerText = childComponent.state._python_type_;

            // Position the child
            let childRect = childComponent.element.getBoundingClientRect();

            let childLeft =
                childRect.left / pixelsPerRem - parentLeftInViewport;
            let childTop = childRect.top / pixelsPerRem - parentTopInViewport;

            childElement.style.left = `${childLeft * scalePerX}%`;
            childElement.style.top = `${childTop * scalePerY}%`;

            // Size the child
            childElement.style.width = `${
                childComponent.allocatedWidth * scalePerX
            }%`;
            childElement.style.height = `${
                childComponent.allocatedHeight * scalePerY
            }%`;

            // Position the margin
            let margins = childComponent.state._margin_;

            let marginLeft = childLeft - margins[0];
            let marginTop = childTop - margins[1];

            marginElement.style.left = `${marginLeft * scalePerX}%`;
            marginElement.style.top = `${marginTop * scalePerY}%`;

            // Size the margin
            marginElement.style.width = `${
                (childComponent.allocatedWidth + margins[0] + margins[2]) *
                scalePerX
            }%`;

            marginElement.style.height = `${
                (childComponent.allocatedHeight + margins[1] + margins[3]) *
                scalePerY
            }%`;

            // Clicking selects the component
            if (!isTarget) {
                childElement.onclick = () => {
                    // Make sure the child id is a number, since this isn't
                    // guaranteed in the frontend
                    console.assert(typeof childComponent.id === 'number');

                    // Update the state
                    this.setStateAndNotifyBackend({
                        component_id: childComponent.id,
                    });
                };
            }

            // Hovering highlights it
            childElement.onmouseenter = () => {
                this.hoveredChild = childComponent.element;
                this.updateHighlighter();
            };

            childElement.onmouseleave = () => {
                if (this.hoveredChild !== childComponent.element) {
                    return;
                }

                this.hoveredChild = null;
                this.updateHighlighter();
            };
        }
    }

    updateHighlighter(): void {
        // If a child is hovered, move the highlighter to it
        if (this.hoveredChild !== null) {
            this.highlighter.moveTo(this.hoveredChild);
            return;
        }

        // Otherwise, if the parent is hovered, highlight it
        if (this.parentIsHovered) {
            let targetComponent: ComponentBase =
                componentsById[this.state.component_id]!;

            if (targetComponent === undefined) {
                this.highlighter.moveTo(null);
                return;
            }

            let parentComponent = targetComponent.getParentExcludingInjected();

            if (parentComponent === null) {
                this.highlighter.moveTo(null);
            } else {
                this.highlighter.moveTo(parentComponent.element);
            }
            return;
        }

        // Otherwise, hide the highlighter
        this.highlighter.moveTo(null);
    }
}
