import { pixelsPerRem } from './app';
import { getRootComponent } from './componentManagement';
import { ComponentBase } from './components/componentBase';

export class LayoutContext {
    _immediateReLayoutCallbacks: (() => void)[] = [];

    private updateRequestedWidthRecursive(component: ComponentBase): void {
        if (!component.isLayoutDirty) return;

        for (let child of component.children) {
            this.updateRequestedWidthRecursive(child);
        }

        component.updateNaturalWidth(this);
        component.requestedWidth = Math.max(
            component.naturalWidth,
            component.state._size_[0]
        );
    }

    private updateAllocatedWidthRecursive(component: ComponentBase): void {
        if (!component.isLayoutDirty) return;

        let children = Array.from(component.children);
        let childAllocatedWidths = children.map(
            (child) => child.allocatedWidth
        );

        component.updateAllocatedWidth(this);

        // The FundamentalRootComponent always has a width of 100vw, so we don't
        // want to assign the width here. We'll only assign the width of this
        // component's children.

        for (let i = 0; i < children.length; i++) {
            let child = children[i];

            if (child.allocatedWidth !== childAllocatedWidths[i]) {
                child.isLayoutDirty = true;
            }

            if (child.isLayoutDirty) {
                this.updateAllocatedWidthRecursive(child);
            }

            let element = child.element;
            element.style.width = `${child.allocatedWidth * pixelsPerRem}px`;
        }
    }

    private updateRequestedHeightRecursive(component: ComponentBase): void {
        if (!component.isLayoutDirty) return;

        for (let child of component.children) {
            this.updateRequestedHeightRecursive(child);
        }

        component.updateNaturalHeight(this);
        component.requestedHeight = Math.max(
            component.naturalHeight,
            component.state._size_[1]
        );
    }

    private updateAllocatedHeightRecursive(component: ComponentBase): void {
        if (!component.isLayoutDirty) return;

        let children = Array.from(component.children);
        let childAllocatedHeights = children.map(
            (child) => child.allocatedHeight
        );

        component.updateAllocatedHeight(this);

        // The FundamentalRootComponent always has a height of 100vh, so we
        // don't want to assign the width here. We'll only assign the height of
        // this component's children.

        for (let i = 0; i < children.length; i++) {
            let child = children[i];

            if (child.allocatedHeight !== childAllocatedHeights[i]) {
                child.isLayoutDirty = true;
            }

            if (child.isLayoutDirty) {
                this.updateAllocatedHeightRecursive(child);
            }

            child.isLayoutDirty = false;

            let element = child.element;
            element.style.height = `${child.allocatedHeight * pixelsPerRem}px`;
        }
    }

    public updateLayout(): void {
        let rootComponent = getRootComponent();

        // Find out how large all components would like to be
        this.updateRequestedWidthRecursive(rootComponent);

        // Note: The FundamentalRootComponent is responsible for allocating the
        // available window space. There is no need to take care of anything
        // here.

        // Distribute the just received width to all children
        this.updateAllocatedWidthRecursive(rootComponent);

        // Now that all components have their width set, find out their height.
        // This is done later on, so that text can request height based on its
        // width.
        this.updateRequestedHeightRecursive(rootComponent);

        // Distribute the just received height to all children
        this.updateAllocatedHeightRecursive(rootComponent);
    }

    /// Signal to the layout engine that it should re-layout the component tree
    /// immediately after the current layout cycle finishes. The given function
    /// will be called before the re-layout happens, allowing the caller to
    /// dirty components or do other things.
    public requestImmediateReLayout(callback: () => void): void {
        this._immediateReLayoutCallbacks.push(callback);
    }
}

export function updateLayout(): void {
    let context = new LayoutContext();

    while (true) {
        // Update the layout
        context.updateLayout();

        // Are any re-layouts requested?
        if (context._immediateReLayoutCallbacks.length === 0) {
            break;
        }

        // Call all hooks
        for (let callback of context._immediateReLayoutCallbacks) {
            callback();
        }

        context._immediateReLayoutCallbacks = [];
    }
}
