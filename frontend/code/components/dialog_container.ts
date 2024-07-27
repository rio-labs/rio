import { ComponentId } from '../dataModels';
import { commitCss } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';

export type DialogContainerState = ComponentState & {
    _type_: 'DialogContainer-builtin';
    content?: ComponentId;
};

export class DialogContainerComponent extends ComponentBase {
    state: Required<DialogContainerState>;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-dialog-container', 'rio-switcheroo-neutral');

        // Since dialog containers aren't part of the component tree, they're
        // themselves responsible for adding themselves to the DOM.
        document.body.appendChild(element);

        // Animate the element
        requestAnimationFrame(() => {
            commitCss(element);
            element.classList.add('rio-dialog-container-enter');
        });

        return element;
    }

    onDestruction(): void {
        // Chain up
        super.onDestruction();

        // Rather than disappearing immediately, the dialog container would like
        // to fade out its content. This doesn't work though, because the
        // content is also deleted when the dialog container is. So create a
        // copy of the container's HTML and animate that instead.
        let phony = this.element.cloneNode(true) as HTMLElement;
        phony.style.pointerEvents = 'none';

        document.body.appendChild(phony);
        commitCss(phony);

        // Animate the element
        phony.classList.remove('rio-dialog-container-enter');

        // Remove the element after the animation is done
        setTimeout(() => {
            phony.remove();
        }, 2000);
    }

    updateElement(
        deltaState: DialogContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);
        this.replaceOnlyChild(latentComponents, deltaState.content);
    }
}
