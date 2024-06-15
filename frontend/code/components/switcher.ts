import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { componentsById } from '../componentManagement';
import { commitCss } from '../utils';

export type SwitcherState = ComponentState & {
    _type_: 'Switcher-builtin';
    content?: ComponentId | null;
    transition_time?: number;
};

export class SwitcherComponent extends ComponentBase {
    state: Required<SwitcherState>;

    private activeChildContainer: HTMLElement | null = null;

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
            deltaState.content !== undefined &&
            deltaState.content !== this.state.content
        ) {
            this.replaceContent(deltaState.content, latentComponents);
        }
    }

    private replaceContent(
        content: ComponentId | null,
        latentComponents: Set<ComponentBase>
    ): void {}

    private removeCurrentChild(latentComponents: Set<ComponentBase>): void {
        if (this.activeChildContainer === null) {
            return;
        }

        // The old component may be used somewhere else in the UI, so the
        // switcher can't rely on it still being available. To get around this,
        // create a copy of the element's HTML tree and use that for the
        // animation.
        //
        // Moreover, the component may have already been removed from the
        // switcher. This can happen when it was moved into another component.
        // Thus, fetch the component by its id, rather than using the contained
        // HTML node.
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
        this.activeChildContainer.classList.remove('rio-switcher-active-child');
        this.activeChildContainer.style.maxWidth = '0';
        this.activeChildContainer.style.maxHeight = '0';

        // Make sure to remove the child after the animation finishes
        let oldChildContainer = this.activeChildContainer;

        setTimeout(() => {
            oldChildContainer.remove();
        }, this.state.transition_time * 1000);

        // No more children :(
        this.activeChildContainer = null;
    }

    private addNewChild(
        content: ComponentId | null,
        latentComponents: Set<ComponentBase>
    ): void {
        if (content === null) {
            return;
        }

        // Add the child into a helper container
        this.activeChildContainer = document.createElement('div');
        this.activeChildContainer.style.maxWidth = '0';
        this.activeChildContainer.style.maxHeight = '0';
        this.element.appendChild(this.activeChildContainer);

        this.replaceOnlyChild(
            latentComponents,
            content,
            this.activeChildContainer
        );

        // Animate the child in
        commitCss(this.activeChildContainer);
        this.activeChildContainer.classList.add('rio-switcher-active-child');

        // The components may currently be in flux due to a pending re-layout.
        // If that is the case, reading the `scrollHeight` would lead to an
        // incorrect value. Wait for the resize to finish before fetching it.
        let activeChildContainer = this.activeChildContainer;

        requestAnimationFrame(() => {
            let contentWidth = activeChildContainer.scrollWidth;
            let selfWidth = this.element.scrollWidth;
            let targetWidth = Math.max(contentWidth, selfWidth);

            let contentHeight = activeChildContainer.scrollHeight;
            let selfHeight = this.element.scrollHeight;
            let targetHeight = Math.max(contentHeight, selfHeight);

            activeChildContainer.style.maxWidth = `${targetWidth}px`;
            activeChildContainer.style.maxHeight = `${targetHeight}px`;

            // Once the animation is finished, remove the max-width/max-height
            // so that the child component can freely resize itself
            setTimeout(() => {
                activeChildContainer.style.removeProperty('max-width');
                activeChildContainer.style.removeProperty('max-height');
            }, this.state.transition_time * 1000);
        });
    }
}
