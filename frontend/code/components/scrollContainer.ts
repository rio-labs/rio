import { ComponentStatesUpdateContext } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type ScrollContainerState = ComponentState & {
    _type_: "ScrollContainer-builtin";
    content: ComponentId;
    scroll_x: "never" | "auto" | "always";
    scroll_y: "never" | "auto" | "always";
    initial_x: number;
    initial_y: number;
    reserve_space_y: boolean;
    sticky_bottom: boolean;
};

export class ScrollContainerComponent extends ComponentBase<ScrollContainerState> {
    private scrollerElement: HTMLElement;
    private childContainer: HTMLElement;
    private scrollAnchor: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-scroll-container");

        this.scrollerElement = document.createElement("div");
        element.appendChild(this.scrollerElement);

        // `sticky_bottom` is implemented via scroll anchoring, so we need a
        // column that contains the child component and the scroll anchor
        let column = document.createElement("div");
        column.classList.add("rio-scroll-container-column");
        this.scrollerElement.appendChild(column);

        this.childContainer = document.createElement("div");
        this.childContainer.classList.add(
            "rio-scroll-container-child-container"
        );
        column.appendChild(this.childContainer);

        this.scrollAnchor = document.createElement("div");
        this.scrollAnchor.classList.add("rio-scroll-container-anchor");
        column.appendChild(this.scrollAnchor);

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
        deltaState: DeltaState<ScrollContainerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(context, deltaState.content, this.childContainer);

        if (deltaState.scroll_x !== undefined) {
            this.element.dataset.scrollX = deltaState.scroll_x;
        }

        if (deltaState.scroll_y !== undefined) {
            this.element.dataset.scrollY = deltaState.scroll_y;
        }

        if (deltaState.reserve_space_y !== undefined) {
            this.scrollerElement.style.scrollbarGutter =
                deltaState.reserve_space_y ? "stable" : "auto";
        }

        if (deltaState.sticky_bottom !== undefined) {
            this.scrollAnchor.style.overflowAnchor = deltaState.sticky_bottom
                ? "auto"
                : "none";
        }
    }
}
