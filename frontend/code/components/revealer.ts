import { applyTextStyleCss, textStyleToCss } from "../cssUtils";
import { applyIcon } from "../designApplication";
import { ComponentId, TextStyle } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { RippleEffect } from "../rippleEffect";
import {
    RioAnimation,
    RioAnimationPlayback,
    RioKeyframeAnimation,
} from "../animations";
import { ComponentStatesUpdateContext } from "../componentManagement";

let HEADER_PADDING: number = 0.3;

export type RevealerState = ComponentState & {
    _type_: "Revealer-builtin";
    header: string | null;
    content: ComponentId;
    header_style: "heading1" | "heading2" | "heading3" | "text" | TextStyle;
    is_open: boolean;
};

export class RevealerComponent extends ComponentBase<RevealerState> {
    private headerElement: HTMLElement;
    private labelElement: HTMLElement;
    private arrowElement: HTMLElement;
    private contentOuterElement: HTMLElement;
    private contentInnerElement: HTMLElement;

    private rippleInstance: RippleEffect;
    private currentAnimation: RioAnimationPlayback | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the HTML
        let element = document.createElement("div");
        element.classList.add("rio-revealer");

        element.innerHTML = `
            <div class="rio-revealer-header">
                <div class="rio-revealer-label"></div>
                <div class="rio-revealer-arrow"></div>
            </div>
            <div class="rio-revealer-content-outer">
                <div class="rio-revealer-content-inner"></div>
            </div>
`;

        // Expose the elements
        this.headerElement = element.querySelector(
            ".rio-revealer-header"
        ) as HTMLElement;

        this.labelElement = this.headerElement.querySelector(
            ".rio-revealer-label"
        ) as HTMLElement;

        this.arrowElement = this.headerElement.querySelector(
            ".rio-revealer-arrow"
        ) as HTMLElement;

        this.contentOuterElement = element.querySelector(
            ".rio-revealer-content-outer"
        ) as HTMLElement;

        this.contentInnerElement = element.querySelector(
            ".rio-revealer-content-inner"
        ) as HTMLElement;

        // Initialize them
        applyIcon(this.arrowElement, "material/expand_more", "currentColor");

        this.rippleInstance = new RippleEffect(element, {
            triggerOnPress: false,
        });

        // Listen for presses
        this.headerElement.onclick = (event) => {
            // Trigger the ripple effect
            this.rippleInstance.trigger(event);

            // Toggle the open state
            this.setStateAndNotifyBackend({
                is_open: !this.state.is_open,
            });
        };

        // Color change on hover/leave
        this.headerElement.onpointerenter = () => {
            this.element.style.background = "var(--rio-local-bg-variant)";
        };

        this.headerElement.onpointerleave = () => {
            this.element.style.removeProperty("background");
        };

        return element;
    }

    updateElement(
        deltaState: DeltaState<RevealerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the header
        if (deltaState.header === null) {
            this.headerElement.style.display = "none";
        } else if (deltaState.header !== undefined) {
            this.headerElement.style.removeProperty("display");
            this.labelElement.textContent = deltaState.header;
        }

        // Update the child
        this.replaceOnlyChild(
            context,
            deltaState.content,
            this.contentInnerElement
        );

        // Update the text style
        if (deltaState.header_style !== undefined) {
            // The text is handled by a helper function
            applyTextStyleCss(
                this.labelElement,
                textStyleToCss(deltaState.header_style)
            );

            // The text style defines the overall scale of the header
            let headerScale: number;
            if (deltaState.header_style === "heading1") {
                headerScale = 2;
            } else if (deltaState.header_style === "heading2") {
                headerScale = 1.5;
            } else if (deltaState.header_style === "heading3") {
                headerScale = 1.2;
            } else if (deltaState.header_style === "text") {
                headerScale = 1;
            } else {
                headerScale = deltaState.header_style.fontSize ?? 1;
            }

            // Adapt the header's padding
            let cssPadding = `${HEADER_PADDING * headerScale}rem`;
            this.headerElement.style.padding = cssPadding;

            // Make the arrow match
            let arrowSize = headerScale * 1.0;
            this.arrowElement.style.width = `${arrowSize}rem`;
            this.arrowElement.style.height = `${arrowSize}rem`;
            this.arrowElement.style.color = this.labelElement.style.color;
        }

        // Expand / collapse
        if (deltaState.is_open !== undefined) {
            // If this component has only just been created, then skip the
            // animation and render the final result immediately
            if (this.contentOuterElement.style.maxHeight === "") {
                if (deltaState.is_open) {
                    this.element.classList.add("rio-revealer-open");
                    this.contentOuterElement.style.maxHeight = "unset";
                } else {
                    this.contentOuterElement.style.maxHeight = "0";
                }
            } else {
                if (deltaState.is_open) {
                    this.animateOpen();
                } else {
                    this.animateClose();
                }
            }
        }
    }

    private animateOpen(): void {
        // Do nothing if already expanded
        if (this.element.classList.contains("rio-revealer-open")) {
            return;
        }

        // The components may currently be in flux due to a pending re-layout.
        // If that is the case, reading the `scrollHeight` would lead to an
        // incorrect value. Wait for the resize to finish before fetching it.
        requestAnimationFrame(() => {
            // Cancel the current animation, if any
            if (this.currentAnimation !== null) {
                this.currentAnimation.cancel();
            }

            // Start the open animation
            let animation = this.makeAnimation("open");
            this.currentAnimation = animation.animate(this.contentOuterElement);

            // The animation requires a specific height to animate to, but this
            // prevents the content from resizing itself. So at the end of the
            // animation, remove the `max-height`.
            this.currentAnimation.addEventListener("end", () => {
                this.contentOuterElement.style.maxHeight = "unset";
            });

            // Update the CSS to trigger all the other animations
            this.element.classList.add("rio-revealer-open");
        });
    }

    private animateClose(): void {
        // Do nothing if already collapsed
        if (!this.element.classList.contains("rio-revealer-open")) {
            return;
        }

        // Cancel the current animation, if any
        if (this.currentAnimation !== null) {
            this.currentAnimation.cancel();
        }

        // Start the close animation
        let animation = this.makeAnimation("close");
        this.currentAnimation = animation.animate(this.contentOuterElement);

        this.element.classList.remove("rio-revealer-open");
    }

    private makeAnimation(mode: "open" | "close"): RioAnimation {
        let keyframes = [
            { maxHeight: "0" },
            // Animating to/from "unset" doesn't work, so we need to obtain the
            // actual height
            { maxHeight: this.getHeightForAnimation() },
        ];

        if (mode === "close") {
            keyframes.reverse();
        }

        return new RioKeyframeAnimation(keyframes, {
            duration: 250,
            easing: "ease-in-out",
        });
    }

    private getHeightForAnimation(): string {
        let contentHeight = this.contentInnerElement.scrollHeight;
        let selfHeight = this.element.scrollHeight;
        let headerHeight = this.headerElement.scrollHeight;
        let targetHeight = Math.max(contentHeight, selfHeight - headerHeight);

        return `${targetHeight}px`;
    }
}
