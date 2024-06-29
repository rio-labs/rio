import { ComponentId } from '../dataModels';
import { NaturalHeightObserver } from '../naturalSizeObservers';
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

    // 'auto'-scrolling in the y direction has a unique problem: Because the
    // width of an element is decided before its height, the browser doesn't
    // know whether a vertical scroll bar will be needed until it's too late. If
    // it turns out that the parent didn't allocate enough width for the child
    // *and* the vertical scroll bar, it will suddenly start scrolling in *both*
    // directions. That's not what we want - we want to increase the parent's
    // width instead.
    //
    // The workaround: Whenever the child's or parent's size changes, check if a
    // vertical scroll bar is needed and set `overflow-y` to `scroll` or
    // `visible` accordingly.
    private childNaturalHeight: number = 0;
    private resizeObserver: ResizeObserver;
    private naturalHeightObserver: NaturalHeightObserver;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-scroll-container');

        this.scrollerElement = document.createElement('div');
        element.appendChild(this.scrollerElement);

        this.naturalHeightObserver = new NaturalHeightObserver(
            this._onChildNaturalHeightChanged.bind(this)
        );
        this.scrollerElement.appendChild(
            this.naturalHeightObserver.outerElement
        );

        this.resizeObserver = new ResizeObserver(
            this._updateScrollY.bind(this)
        );
        this.resizeObserver.observe(this.scrollerElement);

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

    onDestruction(): void {
        this.resizeObserver.disconnect();
        this.naturalHeightObserver.destroy();
    }

    updateElement(
        deltaState: ScrollContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.naturalHeightObserver.innerElement
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

    private _onChildNaturalHeightChanged(naturalHeight: number): void {
        this.childNaturalHeight = naturalHeight;
        this._updateScrollY();
    }

    private _updateScrollY(): void {
        this.element.dataset.scrollY =
            this.childNaturalHeight > this.scrollerElement.clientHeight + 1
                ? 'always'
                : 'never';
    }
}
