import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { componentsById } from '../componentManagement';
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
        super.updateElement(deltaState, latentComponents);

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
    }
}
