import { textStyleToCss } from "../cssUtils";
import { applyIcon } from "../designApplication";
import { ComponentId, TextStyle } from "../dataModels";
import { commitCss } from "../utils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { RippleEffect } from "../rippleEffect";

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

    createElement(): HTMLElement {
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
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the header
        if (deltaState.header === null) {
            this.headerElement.style.display = "none";
        } else if (deltaState.header !== undefined) {
            this.headerElement.style.removeProperty("display");
            this.labelElement.textContent = deltaState.header;
        }

        // Update the child
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.contentInnerElement
        );

        // Update the text style
        if (deltaState.header_style !== undefined) {
            // The text is handled by a helper function
            Object.assign(
                this.labelElement.style,
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
                headerScale = deltaState.header_style.fontSize;
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

        // Update the CSS to trigger the expand animation
        this.contentOuterElement.style.maxHeight = "0";
        this.element.classList.add("rio-revealer-open");

        // The components may currently be in flux due to a pending re-layout.
        // If that is the case, reading the `scrollHeight` would lead to an
        // incorrect value. Wait for the resize to finish before fetching it.
        requestAnimationFrame(() => {
            // Animating max-height only works with fixed values (and not
            // `unset`, etc), so we have to assign the child's exact height in
            // pixels
            this.setMaxHeightToChildHeight();

            // Once the animation is finished, remove the max-height so that the
            // child component can freely resize itself
            setTimeout(() => {
                this.contentOuterElement.style.maxHeight = "unset";
            }, 1000 * 0.25);
        });
    }

    private animateClose(): void {
        // Do nothing if already collapsed
        if (!this.element.classList.contains("rio-revealer-open")) {
            return;
        }

        // Again, animating from `max-height: unset` doesn't work, so we have to
        // set it to the child's size in pixels
        this.setMaxHeightToChildHeight();
        commitCss(this.contentOuterElement);

        this.element.classList.remove("rio-revealer-open");
        this.contentOuterElement.style.maxHeight = "0";
    }

    private setMaxHeightToChildHeight(): void {
        let contentHeight = this.contentInnerElement.scrollHeight;
        let selfHeight = this.element.scrollHeight;
        let headerHeight = this.headerElement.scrollHeight;
        let targetHeight = Math.max(contentHeight, selfHeight - headerHeight);

        this.contentOuterElement.style.maxHeight = `${targetHeight}px`;
    }
}
