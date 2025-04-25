import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { easeIn, easeInOut, easeOut } from "../easeFunctions";
import { ComponentId } from "../dataModels";
import { ComponentStatesUpdateContext } from "../componentManagement";

const switchDuration = 0.8;
const progressBarFadeDuration = 0.2;

export type SlideshowState = ComponentState & {
    _type_: "Slideshow-builtin";
    children: ComponentId[];
    linger_time: number;
    pause_on_hover: boolean;
    corner_radius: [number, number, number, number];
};

export class SlideshowComponent extends ComponentBase<SlideshowState> {
    private childContainer: HTMLElement;
    private progressBar: HTMLElement;

    private isHovered: boolean = false;
    private lastUpdateAt: number;

    private currentChildIndex: number = 0;
    private incomingChild: HTMLElement;
    private outgoingChild: HTMLElement;

    private waitTimeProgress: number = 0;
    private switchProgress: number = 0;

    private progressBarOpacity: number = 1;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the elements
        let element = document.createElement("div");
        element.classList.add("rio-slideshow");

        element.innerHTML = `
<div class="slideshow-child-container">
</div>
<div class="slideshow-progress"> </div>
`;

        // Store them for easy access
        this.childContainer = element.querySelector(
            ".slideshow-child-container"
        ) as HTMLElement;

        this.progressBar = element.querySelector(
            ".slideshow-progress"
        ) as HTMLElement;

        // Connect to events
        element.addEventListener("pointerenter", () => {
            this.isHovered = true;
        });

        element.addEventListener("pointerleave", () => {
            this.isHovered = false;
        });

        // Initialize state
        this.lastUpdateAt = Date.now() / 1000;

        // Start the update loop
        requestAnimationFrame(this.updateLoop.bind(this));

        return element;
    }

    updateElement(
        deltaState: DeltaState<SlideshowState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the children
        if (deltaState.children !== undefined) {
            this.replaceChildren(
                context,
                deltaState.children,
                this.childContainer,
                true
            );

            // Make sure no children are hiding the current one
            //
            // It's fine to hide all of them. The update loop will take care to
            // show the correct one(s).
            let ii = 0;
            for (let child of Array.from(this.childContainer.children)) {
                if (!(child instanceof HTMLElement)) {
                    continue;
                }

                if (ii == this.currentChildIndex) {
                    child.style.transform = "translateX(0%)";
                } else {
                    child.style.transform = "translateX(-100%)";
                }

                ++ii;
            }
        }

        // Corner radius
        if (deltaState.corner_radius !== undefined) {
            let [topLeft, topRight, bottomRight, bottomLeft] =
                deltaState.corner_radius;

            this.element.style.borderRadius = `${topLeft}rem ${topRight}rem ${bottomRight}rem ${bottomLeft}rem`;
        }
    }

    private get isPaused(): boolean {
        return this.state.pause_on_hover && this.isHovered;
    }

    async updateLoop() {
        // If the slideshow has been removed from the DOM, stop updating
        if (!this.element.isConnected) {
            return;
        }

        // How much time has passed since the last update?
        const now = Date.now() / 1000;
        const passedTime = now - this.lastUpdateAt;

        // Special case: If there's only one child, there's nothing to do
        //@ts-ignore
        let children: Array<HTMLElement> = Array.from(
            this.childContainer.children
        );
        if (children.length <= 1) {
            this.lastUpdateAt = now;
            requestAnimationFrame(this.updateLoop.bind(this));
            return;
        }

        // Case 1: Currently switching to the next child
        if (this.waitTimeProgress == 1) {
            // Update the progress
            this.switchProgress = Math.min(
                this.switchProgress + passedTime / switchDuration,
                1
            );

            // Update the animated children's positions
            let offset = easeInOut(this.switchProgress);
            this.outgoingChild.style.transform = `translateX(${
                -100 * offset
            }%)`;
            this.incomingChild.style.transform = `translateX(${
                -100 * (offset - 1)
            }%)`;

            // Update the progress bar's opacity
            this.progressBarOpacity = Math.max(
                this.progressBarOpacity - passedTime / progressBarFadeDuration,
                0
            );
            this.progressBar.style.opacity = easeOut(
                this.progressBarOpacity
            ).toString();

            // If the progress has hit 100%, the switch is complete
            if (this.switchProgress == 1) {
                this.waitTimeProgress = 0;
                this.progressBarOpacity = 1;
            }
        }

        // Case 2: Waiting for the next switch
        else if (!this.isPaused) {
            // Update the progress
            this.waitTimeProgress = Math.min(
                this.waitTimeProgress + passedTime / this.state.linger_time,
                1
            );

            // Update the progress bar's width
            this.progressBar.style.width = `${this.waitTimeProgress * 100}%`;

            // Update the progress bar's opacity
            this.progressBarOpacity = Math.min(
                this.progressBarOpacity + passedTime / progressBarFadeDuration,
                1
            );
            this.progressBar.style.opacity = easeIn(
                this.progressBarOpacity
            ).toString();

            // If the progress has hit 100%, it's time to switch to the next
            // child
            if (this.waitTimeProgress == 1) {
                this.switchProgress = 0;
                this.outgoingChild = children[this.currentChildIndex];
                this.currentChildIndex =
                    (this.currentChildIndex + 1) % children.length;
                this.incomingChild = children[this.currentChildIndex];
            }
        }

        // Case 3: The slideshow is paused
        else {
            // Calculate the progress bar's opacity
            this.progressBarOpacity = Math.max(
                this.progressBarOpacity - passedTime / progressBarFadeDuration,
                0
            );
            this.progressBar.style.opacity = easeOut(
                this.progressBarOpacity
            ).toString();

            // If the progress bar is completely invisible, it is now safe to
            // reset progress without a visual glitch
            if (this.progressBarOpacity === 0) {
                this.waitTimeProgress = 0;
            }
        }

        // Housekeeping
        this.lastUpdateAt = now;
        requestAnimationFrame(this.updateLoop.bind(this));
    }
}
