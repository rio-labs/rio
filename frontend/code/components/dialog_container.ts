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
        console.debug('DESTROYED!');

        // Remove the element from the DOM
        this.element.remove();
    }

    updateElement(
        deltaState: DialogContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);
        this.replaceOnlyChild(latentComponents, deltaState.content);
    }
}
