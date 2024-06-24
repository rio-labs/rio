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

export class ScrollContainerComponent extends ComponentBase {
    state: Required<ScrollContainerState>;

    // Sometimes components are temporarily removed from the DOM or resized (for
    // example, `getElementDimensions` does both), which can lead to the scroll
    // position being changed or reset. In order to prevent this, we'll wrap our
    // child in a container element.
    private childContainer: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-scroll');

        let helperElement = document.createElement('div');
        element.appendChild(helperElement);

        this.childContainer = document.createElement('div');
        helperElement.appendChild(this.childContainer);

        return element;
    }

    updateElement(
        deltaState: ScrollContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.childContainer
        );

        if (deltaState.scroll_x !== undefined) {
            this.element.dataset.scrollX = deltaState.scroll_x;
        }

        if (deltaState.scroll_y !== undefined) {
            this.element.dataset.scrollY = deltaState.scroll_y;
        }
    }
}
