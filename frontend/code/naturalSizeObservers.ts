/// This module contains classes that act as a container for a child
/// element, and also notify you if the child's natural width/height changes.
///
/// How does that work? The concept is simple:
///
/// - Create a flexbox container element that is too large for the child
/// - Add the child and a spacer element to the container
/// - Calculate the flex-grow of the child and the spacer such that the spacer
///   takes up all of the extra space
/// - Add another element with `overflow: hidden` to hide the spacer
///
/// Since the child's natural size is used as the flex-basis, a change in its
/// natural size will also change its allocated size. This change can be
/// observed with a ResizeObserver.

import { getAllocatedHeightInPx } from "./utils";

const TARGET_SPACER_SIZE = 30;

export class NaturalHeightObserver {
    public outerElement: HTMLElement;
    public innerElement: HTMLElement;

    private flexbox: HTMLElement;

    private onNaturalHeightChange: (naturalHeight: number) => void;

    private childSizeObserver: ResizeObserver;
    private previousChildHeight = -1;

    private flexboxSizeObserver: ResizeObserver;
    private previousFlexboxHeight = -1;

    private previousNaturalHeight = -1;

    constructor(onNaturalHeightChange: (naturalHeight: number) => void) {
        this.onNaturalHeightChange = onNaturalHeightChange;

        this.outerElement = document.createElement("div");
        this.outerElement.classList.add("rio-natural-height-observer");

        this.outerElement.innerHTML = `
        <div class="rio-natural-height-observer-flexbox">
            <div class="rio-natural-size-observer-child-container"></div>
            <div class="rio-natural-size-observer-spacer"></div>
        </div>
        `;

        this.flexbox = this.outerElement.querySelector(
            ".rio-natural-height-observer-flexbox"
        ) as HTMLElement;
        this.flexbox.style.height = `calc(100% + ${TARGET_SPACER_SIZE}px)`;

        this.innerElement = this.outerElement.querySelector(
            ".rio-natural-size-observer-child-container"
        ) as HTMLElement;

        this.childSizeObserver = new ResizeObserver(
            this._onChildResized.bind(this)
        );
        this.childSizeObserver.observe(this.innerElement);

        // Also observe the parent element's size. If the child's flex-grow was
        // calculated to be 0, it won't automatically trigger when its parent
        // grows.
        this.flexboxSizeObserver = new ResizeObserver(
            this._onFlexboxResized.bind(this)
        );
        this.flexboxSizeObserver.observe(this.flexbox);
    }

    public destroy(): void {
        this.childSizeObserver.disconnect();
        this.flexboxSizeObserver.disconnect();
    }

    private _onChildResized(): void {
        let newHeight = this.innerElement.scrollHeight;

        if (newHeight === this.previousChildHeight) {
            return;
        }

        this.relayout();
    }

    private _onFlexboxResized(): void {
        let flexboxHeight = getAllocatedHeightInPx(this.flexbox);

        if (flexboxHeight === this.previousFlexboxHeight) {
            return;
        }

        this.relayout();
    }

    private relayout(): void {
        this.childSizeObserver.disconnect();

        // Figure out the child's natural height
        this.innerElement.style.flexGrow = "0";
        let naturalHeight = getAllocatedHeightInPx(this.innerElement);

        let flexboxHeight = getAllocatedHeightInPx(this.flexbox);

        // Calculate the flex-grow
        let extraHeight = flexboxHeight - naturalHeight;
        let flexGrow = extraHeight / TARGET_SPACER_SIZE - 1;
        flexGrow = Math.max(0, flexGrow);

        this.innerElement.style.flexGrow = `${flexGrow}`;
        this.outerElement.style.minHeight = `${naturalHeight}px`;

        // Call the callback function if necessary
        if (naturalHeight !== this.previousNaturalHeight) {
            this.onNaturalHeightChange(naturalHeight);
        }

        // Bookkeeping
        this.previousChildHeight = this.innerElement.scrollHeight;
        this.previousFlexboxHeight = flexboxHeight;
        this.previousNaturalHeight = naturalHeight;

        this.childSizeObserver.observe(this.innerElement);
    }
}
