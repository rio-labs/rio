import { pixelsPerRem, scrollBarSize } from '../app';
import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type ScrollContainerState = ComponentState & {
    _type_: 'ScrollContainer-builtin';
    content?: ComponentId;
    scroll_x?: 'never' | 'auto' | 'always';
    scroll_y?: 'never' | 'auto' | 'always';
    initial_x?: number;
    initial_y?: number;
    sticky_bottom?: boolean;
};

const NATURAL_SIZE = 1.0;

export class ScrollContainerComponent extends ComponentBase {
    state: Required<ScrollContainerState>;

    // Sometimes components are temporarily removed from the DOM or resized (for
    // example, `getElementDimensions` does both), which can lead to the scroll
    // position being changed or reset. In order to prevent this, we'll wrap our
    // child in a container element.
    private childContainer: HTMLElement;

    private isFirstLayout: boolean = true;
    private assumeVerticalScrollBarWillBeNeeded: boolean = true;
    private numSequentialIncorrectAssumptions: number = 0;
    private wasScrolledToBottom: boolean | null = null;

    private shouldLayoutWithVerticalScrollbar(): boolean {
        switch (this.state.scroll_y) {
            case 'always':
                return true;

            case 'auto':
                return this.assumeVerticalScrollBarWillBeNeeded;

            case 'never':
                return false;
        }
    }

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-scroll-container');

        this.childContainer = document.createElement('div');
        element.appendChild(this.childContainer);

        return element;
    }

    updateElement(
        deltaState: ScrollContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.childContainer
        );
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        if (this.state.scroll_x === 'never') {
            let child = componentsById[this.state.content]!;
            this.naturalWidth = child.requestedWidth;
        } else {
            this.naturalWidth = NATURAL_SIZE;
        }

        // If there will be a vertical scroll bar, reserve space for it
        if (this.shouldLayoutWithVerticalScrollbar()) {
            this.naturalWidth += scrollBarSize;
        }
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        let child = componentsById[this.state.content]!;

        // If `sticky_bottom` is enabled, we need to find out whether we're
        // scrolled all the way to the bottom before we change the child's
        // allocation.
        //
        // We can't do this in `updateNaturalWidth` because the layouting
        // algorithm doesn't always call that method.
        if (
            this.state.sticky_bottom &&
            this.numSequentialIncorrectAssumptions === 0
        ) {
            this.wasScrolledToBottom = this._checkIfScrolledToBottom(child);
        }

        let availableWidth = this.allocatedWidth;
        if (this.shouldLayoutWithVerticalScrollbar()) {
            availableWidth -= scrollBarSize;
        }

        // If the child needs more space than we have, we'll need to display a
        // scroll bar. So just give the child the width it wants.
        if (child.requestedWidth > availableWidth) {
            child.allocatedWidth = child.requestedWidth;
            this.element.style.overflowX = 'scroll';
        } else {
            // Otherwise, stretch the child to use up all the available width
            child.allocatedWidth = availableWidth;

            this.element.style.overflowX =
                this.state.scroll_x === 'always' ? 'scroll' : 'hidden';
        }

        this.childContainer.style.width = `${child.allocatedWidth}rem`;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        if (this.state.scroll_y === 'never') {
            let child = componentsById[this.state.content]!;
            this.naturalHeight = child.requestedHeight;
        } else {
            this.naturalHeight = NATURAL_SIZE;
        }

        // If there will be a horizontal scroll bar, reserve space for it
        if (this.element.style.overflowX === 'scroll') {
            this.naturalHeight += scrollBarSize;
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        let child = componentsById[this.state.content]!;

        let availableHeight = this.allocatedHeight;
        if (this.element.style.overflowX === 'scroll') {
            availableHeight -= scrollBarSize;
        }

        // If the child needs more space than we have, we'll need to display a
        // scroll bar. So just give the child the height it wants.
        let newAllocatedHeight: number;
        if (child.requestedHeight > availableHeight) {
            newAllocatedHeight = child.requestedHeight;
            this.element.style.overflowY = 'scroll';
        } else {
            // Otherwise, stretch the child to use up all the available height
            newAllocatedHeight = availableHeight;

            if (this.state.scroll_y === 'always') {
                this.element.style.overflowY = 'scroll';
            } else {
                this.element.style.overflowY = 'hidden';
            }
        }

        // Now check if our assumption for the vertical scroll bar was correct.
        // If not, we have to immediately re-layout the child.
        let hasVerticalScrollbar = this.element.style.overflowY === 'scroll';
        if (
            this.state.scroll_y === 'auto' &&
            this.assumeVerticalScrollBarWillBeNeeded !== hasVerticalScrollbar
        ) {
            // Theoretically, there could be a situation where our assumptions
            // are always wrong and we re-layout endlessly.
            //
            // It's acceptable to have an unnecessary scroll bar, but it's not
            // acceptable to be missing a scroll bar when one is required. So we
            // will only re-layout if this is the first time our assumption was
            // wrong, or if we don't currently have a scroll bar.
            if (
                this.numSequentialIncorrectAssumptions == 0 ||
                !this.assumeVerticalScrollBarWillBeNeeded
            ) {
                this.numSequentialIncorrectAssumptions++;
                this.assumeVerticalScrollBarWillBeNeeded =
                    !this.assumeVerticalScrollBarWillBeNeeded;

                // While a re-layout is about to be requested, this doesn't mean
                // that the current layouting process won't continue. Assign a
                // reasonable amount of space to the child so any subsequent
                // layouting functions don't crash because of unassigned values.
                //
                // The exact value doesn't matter, but this one is noticeable
                // when debugging and easy to find in the code.
                child.allocatedHeight = 7.77777777;

                // Then, request a re-layout
                ctx.requestImmediateReLayout(() => {
                    this.makeLayoutDirty();
                });
                return;
            }
        }

        this.numSequentialIncorrectAssumptions = 0;

        // Only change the allocatedHeight once we're sure that we won't be
        // re-layouting again
        child.allocatedHeight = newAllocatedHeight;
        this.childContainer.style.height = `${child.allocatedHeight}rem`;

        if (this.isFirstLayout) {
            this.isFirstLayout = false;

            // Our CSS `height` hasn't been updated yet, so we can't scroll
            // down any further. We must assign the `height` manually.
            this.element.style.height = `${this.allocatedHeight}rem`;

            this.element.scroll({
                top:
                    (child.allocatedHeight - this.allocatedHeight) *
                    pixelsPerRem *
                    this.state.initial_y,
                left:
                    (child.allocatedWidth - this.allocatedWidth) *
                    pixelsPerRem *
                    this.state.initial_x,
                behavior: 'instant',
            });
        }
        // If `sticky_bottom` is enabled, check if we have to scroll down
        else if (this.state.sticky_bottom && this.wasScrolledToBottom) {
            // Our CSS `height` hasn't been updated yet, so we can't scroll
            // down any further. We must assign the `height` manually.
            this.element.style.height = `${this.allocatedHeight}rem`;

            this.element.scroll({
                top: child.allocatedHeight * pixelsPerRem + 999,
                left: this.element.scrollLeft,
                behavior: 'instant',
            });
        }
    }

    private _checkIfScrolledToBottom(child: ComponentBase): boolean {
        // Calculate how much of the child is visible
        let visibleHeight = this.allocatedHeight;
        if (this.element.style.overflowX === 'scroll') {
            visibleHeight -= scrollBarSize;
        }

        return (
            (this.element.scrollTop + 1) / pixelsPerRem + visibleHeight >=
            child.allocatedHeight - 0.00001
        );
    }
}
