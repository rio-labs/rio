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

    // This is the element where the `overflow` setting is applied
    private scrollerElement: HTMLElement;

    private childContainer: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-scroll');

        this.scrollerElement = document.createElement('div');
        element.appendChild(this.scrollerElement);

        let helperElement = document.createElement('div');
        helperElement.classList.add('rio-scroll-container-column');
        this.scrollerElement.appendChild(helperElement);

        this.childContainer = document.createElement('div');
        this.childContainer.classList.add('rio-single-container');
        helperElement.appendChild(this.childContainer);

        // Once the layouting is done, scroll to the initial position
        requestAnimationFrame(() => {
            this.scrollerElement.scrollLeft =
                this.state.initial_x *
                (this.scrollerElement.scrollWidth -
                    this.scrollerElement.clientWidth);

            this.scrollerElement.scrollTop =
                this.state.initial_y *
                (this.scrollerElement.scrollHeight -
                    this.scrollerElement.clientHeight);
        });

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

        if (deltaState.sticky_bottom !== undefined) {
            // Note: CSS has a `overflow-anchor` thing which is supposed to help
            // with this, but I couldn't get it to work. I think it only works
            // if new elements are added (as direct children of the scrolling
            // element).
        }
    }
}
