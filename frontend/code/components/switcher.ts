import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { componentsById } from '../componentManagement';
import { LayoutContext, updateLayout } from '../layouting';
import { easeInOut } from '../easeFunctions';
import { commitCss } from '../utils';

export type SwitcherState = ComponentState & {
    _type_: 'Switcher-builtin';
    content?: ComponentId | null;
    transition_time?: number;
};

export class SwitcherComponent extends ComponentBase {
    state: Required<SwitcherState>;

    // The width and height the child requested before the animation started.
    private previousChildRequestedWidth: number = 0;
    private previousChildRequestedHeight: number = 0;

    // If true, the current layout operation isn't meant for actually laying out
    // the UI, but rather for determining which size the child will receive once
    // the animation finishes.
    private isDeterminingLayout: boolean = true;

    // The width and height the switcher was at before starting the animation.
    private initialRequestedWidth: number;
    private initialRequestedHeight: number;

    // -1 if no animation is running
    private animationStartedAt: number = -1;

    private activeChildInstance: ComponentBase | null = null;
    private activeChildContainer: HTMLElement | null = null;

    private isInitialized: boolean = false;
    private hasBeenLaidOut: boolean = false;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-switcher');

        return element;
    }

    updateElement(
        deltaState: SwitcherState,
        latentComponents: Set<ComponentBase>
    ): void {
        // FIXME: Too low transition times cause issues for some reason.
        // Until that is fixed, clamp the value.
        if (
            deltaState.transition_time !== undefined &&
            deltaState.transition_time < 0.01
        ) {
            deltaState.transition_time = 0.01;
        }

        // Update the transition time first, in case the code below is about
        // to start an animation.
        if (deltaState.transition_time !== undefined) {
            this.element.style.setProperty(
                '--rio-switcher-transition-time',
                `${deltaState.transition_time}s`
            );
        }

        // Update the child
        if (
            !this.isInitialized ||
            (deltaState.content !== undefined &&
                deltaState.content !== this.state.content)
        ) {
            console.assert(deltaState.content !== undefined);

            // Out with the old
            if (this.activeChildContainer !== null) {
                // The old component may be used somewhere else in the UI, so
                // the switcher can't rely on it still being available. To get
                // around this, create a copy of the element's HTML tree and use
                // that for the animation.
                //
                // Moreover, teh component may have already been removed from
                // the switcher. This can happen when it was moved into another
                // component. Thus, fetch the component by its id, rather than
                // using the contained HTML node.
                let oldComponent = componentsById[this.state.content!]!;
                let oldElementClone = oldComponent.element.cloneNode(
                    true
                ) as HTMLElement;

                // Discard the old component
                this.replaceOnlyChild(
                    latentComponents,
                    null,
                    this.activeChildContainer
                );

                // Animate out the old component
                this.activeChildContainer.appendChild(oldElementClone);
                this.activeChildContainer.classList.remove(
                    'rio-switcher-active'
                );

                // Make sure to remove the child after the animation finishes
                let oldChildContainer = this.activeChildContainer;

                setTimeout(() => {
                    oldChildContainer.remove();
                }, this.state.transition_time * 1000);

                // No more children :(
                this.activeChildContainer = null;
                this.activeChildInstance = null;
            }

            // In with the new
            if (deltaState.content === null) {
                this.activeChildContainer = null;
                this.activeChildInstance = null;
            } else {
                // Add the child into a helper container
                this.activeChildContainer = document.createElement('div');
                this.activeChildContainer.style.left = '0';
                this.activeChildContainer.style.top = '0';
                this.element.appendChild(this.activeChildContainer);

                this.replaceOnlyChild(
                    latentComponents,
                    deltaState.content,
                    this.activeChildContainer
                );

                // Remember the child, as it is needed frequently
                this.activeChildInstance = componentsById[deltaState.content!]!;

                // Animate the child in
                commitCss(this.activeChildContainer);
                this.activeChildContainer.classList.add('rio-switcher-active');
            }

            // Start the layouting process
            this.makeLayoutDirty();
        }

        // The component is now initialized
        this.isInitialized = true;
    }

    startAnimationIfNotRunning(): void {
        // Do nothing if the animation is already running
        if (this.animationStartedAt !== -1) {
            return;
        }

        this.animationStartedAt = Date.now();

        requestAnimationFrame(() => {
            this.makeLayoutDirty();
            updateLayout();
        });
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        // If the child's requested size has changed, start the animation
        let childRequestedWidth: number, childRequestedHeight: number;

        if (this.activeChildInstance === null) {
            childRequestedWidth = 0;
            childRequestedHeight = 0;
        } else {
            childRequestedWidth = this.activeChildInstance.requestedWidth;
            childRequestedHeight = this.activeChildInstance.requestedHeight;
        }

        if (
            this.previousChildRequestedWidth !== childRequestedWidth ||
            this.previousChildRequestedHeight !== childRequestedHeight
        ) {
            this.isDeterminingLayout = true;
            this.previousChildRequestedWidth = childRequestedWidth;
            this.previousChildRequestedHeight = childRequestedHeight;
        }

        // Case: Trying to determine the size the child will receive once the
        // animation finishes
        if (this.isDeterminingLayout) {
            this.naturalWidth = childRequestedWidth;
            return;
        }

        // Case: animated layouting
        let now = Date.now();
        let linearT = Math.min(
            1,
            (now - this.animationStartedAt) / 1000 / this.state.transition_time
        );
        let easedT = easeInOut(linearT);

        this.naturalWidth =
            this.initialRequestedWidth +
            easedT * (childRequestedWidth - this.initialRequestedWidth);

        this.naturalHeight =
            this.initialRequestedHeight +
            easedT * (childRequestedHeight - this.initialRequestedHeight);

        // Keep going?
        if (linearT < 1) {
            requestAnimationFrame(() => {
                this.makeLayoutDirty();
                updateLayout();
            });
        } else {
            this.initialRequestedWidth = Math.max(
                this.naturalWidth,
                this.state._size_[0]
            );
            this.initialRequestedHeight = Math.max(
                this.naturalHeight,
                this.state._size_[1]
            );
            this.animationStartedAt = -1;
        }
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // Case: Trying to determine the size the child will receive once the
        // animation finishes
        // OR
        // Case: The parent component resized us
        if (this.isDeterminingLayout || this.animationStartedAt === -1) {
            if (this.activeChildInstance !== null) {
                this.activeChildInstance.allocatedWidth = this.allocatedWidth;
            }
            return;
        }

        // Case: animated layouting
        //
        // Nothing to do here
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // Case: Trying to determine the size the child will receive once the
        // animation finishes
        if (this.isDeterminingLayout) {
            this.naturalHeight =
                this.activeChildInstance === null
                    ? 0
                    : this.activeChildInstance.requestedHeight;
            return;
        }

        // Case: animated layouting
        //
        // Already handled above
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Case: Trying to determine the size the child will receive once the
        // animation finishes
        if (this.isDeterminingLayout) {
            if (this.activeChildInstance !== null) {
                this.activeChildInstance.allocatedHeight = this.allocatedHeight;
            }

            this.isDeterminingLayout = false;

            // If this is the first layout don't animate, just assume the
            // correct size
            if (!this.hasBeenLaidOut) {
                this.hasBeenLaidOut = true;
                this.initialRequestedWidth = this.allocatedWidth;
                this.initialRequestedHeight = this.allocatedHeight;
                return;
            }

            // Start the animation
            if (this.animationStartedAt === -1) {
                this.animationStartedAt = Date.now();
            }

            ctx.requestImmediateReLayout(() => {
                this.makeLayoutDirty();
            });
            return;
        }

        // Case: The parent component resized us
        if (this.animationStartedAt === -1) {
            if (this.activeChildInstance !== null) {
                this.activeChildInstance.allocatedHeight = this.allocatedHeight;
            }
            return;
        }

        // Case: animated layouting
        //
        // Nothing to do here
    }
}
