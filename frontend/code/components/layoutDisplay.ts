import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import {
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import { getDisplayableChildren } from "../devToolsTreeWalk";
import { Highlighter } from "../highlighter";
import { Debouncer } from "../debouncer";
import { markEventAsHandled } from "../eventHandling";
import { pixelsPerRem } from "../app";
import { getAllocatedHeightInPx, getAllocatedWidthInPx } from "../utils";

export type LayoutDisplayState = ComponentState & {
    _type_: "LayoutDisplay-builtin";
    component_id: number;
    max_requested_height: number;
};

export class LayoutDisplayComponent extends ComponentBase<LayoutDisplayState> {
    // Represents the target component's parent. It matches the aspect ratio of
    // the parent and is centered within this component.
    parentElement: HTMLElement;

    // Helper class for highlighting components
    highlighter: Highlighter;

    // Keep track of which element the user is currently hovering over
    parentIsHovered: boolean = false;
    hoveredChild: HTMLElement | null = null;

    // The display has to update when any of the displayed components change
    // size. This are the parameters used to connect/disconnect event handlers
    // for this purpose.
    childrenToWatch: [HTMLElement, () => void][] = [];

    onChangeLimiter: Debouncer;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Initialize the HTML
        let element = document.createElement("div");
        element.classList.add("rio-layout-display");

        this.parentElement = document.createElement("div");
        this.parentElement.classList.add("rio-layout-display-parent");
        element.appendChild(this.parentElement);

        // Create the highlighter
        this.highlighter = new Highlighter();

        // Listen to pointer events
        this.parentElement.onpointerenter = () => {
            this.parentIsHovered = true;
            this.updateHighlighter();
        };

        this.parentElement.onpointerleave = () => {
            this.parentIsHovered = false;
            this.updateHighlighter();
        };

        this.parentElement.ondblclick = (event) => {
            markEventAsHandled(event);

            // Try to find the parent
            let targetComponent: ComponentBase =
                componentsById[this.state.component_id];
            if (targetComponent === undefined) {
                return;
            }

            if (targetComponent.parent === null) {
                return;
            }

            // Switch to it
            this.setStateAndNotifyBackend({
                component_id: targetComponent.parent.id,
            });
        };

        // Create a rate-limited version of the notifyBackendOfChange function
        this.onChangeLimiter = new Debouncer({
            callback: this._notifyBackendOfChange.bind(this),
        });

        // Initialize the content
        setTimeout(() => {
            this.updateContent();
        }, 0);

        // Done
        return element;
    }

    onDestruction(): void {
        super.onDestruction();

        // Destroy the highlighter
        this.highlighter.destroy();
    }

    updateElement(
        deltaState: DeltaState<LayoutDisplayState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Has the target component changed?
        if (deltaState.component_id !== undefined) {
            // Update the content
            //
            // This is necessary because the layout update may not trigger a
            // content update if none of the watched children have changed.
            //
            // Also don't do it straight away, because layouting must happen
            // first, and the other components may not even have had time to
            // update yet.
            setTimeout(() => {
                this.updateContent();
            }, 0);
        }

        // Has the maximum height changed?
        if (deltaState.max_requested_height !== undefined) {
            this.parentElement.style.maxHeight = `${deltaState.max_requested_height}rem`;
        }
    }

    _notifyBackendOfChange(): void {
        this.sendMessageToBackend({
            type: "layoutChange",
        });
    }

    disconnectEventHandlers(): void {
        for (let [element, handler] of this.childrenToWatch) {
            element.removeEventListener("resize", handler);
        }

        this.childrenToWatch = [];
    }

    listenForSizeChange(element: HTMLElement, handler: () => void): void {
        element.addEventListener("resize", handler);
    }

    /// Called by the global dev tools connector when a re-layout was just
    /// performed.
    public onLayoutChange(): void {
        // Update the content
        setTimeout(() => {
            this.updateContent();
        }, 0);

        // Tell the backend about it
        this.onChangeLimiter.call();
    }

    updateContent(): void {
        // Remove any previous content
        this.parentElement.innerHTML = "";

        // No longer care about any currently watched children
        this.disconnectEventHandlers();

        // Get a reference to the target component
        let targetComponent: ComponentBase =
            componentsById[this.state.component_id]!;

        if (targetComponent === undefined) {
            return;
        }

        // Look up the parent
        let parentComponent = targetComponent.parent;
        let parentLayout: number[];

        if (parentComponent === null) {
            parentLayout = [0, 0, window.innerWidth, window.innerHeight];
        } else {
            let parentRect = parentComponent.element.getBoundingClientRect();
            parentLayout = [
                parentRect.left,
                parentRect.top,
                getAllocatedWidthInPx(parentComponent.element),
                getAllocatedHeightInPx(parentComponent.element),
            ];

            this.listenForSizeChange(
                parentComponent.element,
                this.onLayoutChange.bind(this)
            );
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

        // Size the parent element
        let selfAspect =
            getAllocatedWidthInPx(this.element) /
            getAllocatedHeightInPx(this.element);
        let parentAspect = parentAllocatedWidth / parentAllocatedHeight;

        this.parentElement.style.aspectRatio = `${parentAspect}`;

        if (selfAspect < parentAspect) {
            this.parentElement.style.width = "100%";
            this.parentElement.style.height = "auto";
        } else {
            this.parentElement.style.width = "auto";
            this.parentElement.style.height = "100%";
        }

        // Decide on a scale. Display everything as large as possible, while
        // fitting it into the allocated space and without distorting the aspect
        // ratio.
        let scalePerX = 100 / parentAllocatedWidth;
        let scalePerY = 100 / parentAllocatedHeight;

        // Add all children
        for (let childComponent of children) {
            // Watch this child
            this.listenForSizeChange(
                childComponent.element,
                this.onLayoutChange.bind(this)
            );

            // Create the HTML representation
            let childElement = document.createElement("div");
            childElement.classList.add("rio-layout-display-child");
            this.parentElement.appendChild(childElement);

            let marginElement = document.createElement("div");
            marginElement.classList.add("rio-layout-display-margin");
            this.parentElement.appendChild(marginElement);

            // Is this the selected component?
            let isTarget = childComponent.id === targetComponent.id;
            if (isTarget) {
                childElement.classList.add("rio-layout-display-target");
            }

            // Label the child
            childElement.innerText = childComponent.state._python_type_;

            // Position the child
            let childRect = childComponent.element.getBoundingClientRect();

            let childLeft = childRect.left - parentLeftInViewport;
            let childTop = childRect.top - parentTopInViewport;

            childElement.style.left = `${childLeft * scalePerX}%`;
            childElement.style.top = `${childTop * scalePerY}%`;

            // Size the child
            childElement.style.width = `${
                getAllocatedWidthInPx(childComponent.element) * scalePerX
            }%`;
            childElement.style.height = `${
                getAllocatedHeightInPx(childComponent.element) * scalePerY
            }%`;

            // Position the margin
            let margins = childComponent.state._margin_;
            let marginLeft = childLeft - margins[0] * pixelsPerRem;
            let marginTop = childTop - margins[1] * pixelsPerRem;

            marginElement.style.left = `${marginLeft * scalePerX}%`;
            marginElement.style.top = `${marginTop * scalePerY}%`;

            // Size the margin
            marginElement.style.width = `${
                (childRect.width + (margins[0] + margins[2]) * pixelsPerRem) *
                scalePerX
            }%`;

            marginElement.style.height = `${
                (childRect.height + (margins[1] + margins[3]) * pixelsPerRem) *
                scalePerY
            }%`;

            // Clicking selects the component
            if (!isTarget) {
                childElement.onclick = (event) => {
                    markEventAsHandled(event);

                    // Update the state
                    this.setStateAndNotifyBackend({
                        component_id: childComponent.id,
                    });
                };
            }

            // Double clicking switches to the component's children
            childElement.ondblclick = (event) => {
                markEventAsHandled(event);

                // Does this component have any children?
                let childChildren = getDisplayableChildren(childComponent);

                if (childChildren.length === 0) {
                    return;
                }

                // Update the state
                this.setStateAndNotifyBackend({
                    component_id: childChildren[0].id,
                });
            };

            // Hovering highlights it
            childElement.onpointerenter = () => {
                this.hoveredChild = childComponent.element;
                this.updateHighlighter();
            };

            childElement.onpointerleave = () => {
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

            if (targetComponent.parent === null) {
                this.highlighter.moveTo(null);
            } else {
                this.highlighter.moveTo(targetComponent.parent.element);
            }
            return;
        }

        // Otherwise, hide the highlighter
        this.highlighter.moveTo(null);
    }
}
