import { textStyleToCss } from '../cssUtils';
import { applyIcon } from '../designApplication';
import { ComponentId, TextStyle } from '../dataModels';
import { firstDefined } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';
import { RippleEffect } from '../rippleEffect';

let HEADER_PADDING: number = 0.3;

export type RevealerState = ComponentState & {
    _type_: 'Revealer-builtin';
    header?: string | null;
    content?: ComponentId;
    header_style?: 'heading1' | 'heading2' | 'heading3' | 'text' | TextStyle;
    is_open: boolean;
};

export class RevealerComponent extends ComponentBase {
    state: Required<RevealerState>;

    // Tracks the progress of the animation. Zero means fully collapsed, one
    // means fully expanded.
    private animationIsRunning: boolean = false;
    private lastAnimationTick: number;
    private openFractionBeforeEase: number = -1; // Initialized on first state update

    private headerElement: HTMLElement;
    private labelElement: HTMLElement;
    private arrowElement: HTMLElement;
    private contentInnerElement: HTMLElement;
    private contentOuterElement: HTMLElement;

    private headerScale: number;
    private labelWidth: number;
    private labelHeight: number;

    private rippleInstance: RippleEffect;

    createElement(): HTMLElement {
        // Create the HTML
        let element = document.createElement('div');
        element.classList.add('rio-revealer');

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
            '.rio-revealer-header'
        ) as HTMLElement;

        this.labelElement = this.headerElement.querySelector(
            '.rio-revealer-label'
        ) as HTMLElement;

        this.arrowElement = this.headerElement.querySelector(
            '.rio-revealer-arrow'
        ) as HTMLElement;

        this.contentInnerElement = element.querySelector(
            '.rio-revealer-content-inner'
        ) as HTMLElement;

        this.contentOuterElement = element.querySelector(
            '.rio-revealer-content-outer'
        ) as HTMLElement;

        // Initialize them
        applyIcon(this.arrowElement, 'material/expand-more', 'currentColor');

        this.rippleInstance = new RippleEffect(element, {
            triggerOnPress: false,
        });

        // Listen for presses
        this.headerElement.onclick = (event) => {
            // Trigger the ripple effect
            this.rippleInstance.trigger(event);

            // Toggle the open state
            this.state.is_open = !this.state.is_open;

            // Notify the backend
            this.setStateAndNotifyBackend({
                is_open: this.state.is_open,
            });

            // Update the CSS
            if (this.state.is_open) {
                element.classList.add('rio-revealer-open');
            } else {
                element.classList.remove('rio-revealer-open');
            }

            // Update the UI
            this.startAnimationIfNotRunning();
        };

        // Color change on hover/leave
        this.headerElement.onmouseenter = () => {
            this.element.style.background = 'var(--rio-local-bg-variant)';
        };

        this.headerElement.onmouseleave = () => {
            this.element.style.removeProperty('background');
        };

        return element;
    }

    updateElement(
        deltaState: RevealerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the header
        if (deltaState.header === null) {
            this.headerElement.style.display = 'none';
        } else if (deltaState.header !== undefined) {
            this.headerElement.style.removeProperty('display');
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
            if (deltaState.header_style === 'heading1') {
                this.headerScale = 2;
            } else if (deltaState.header_style === 'heading2') {
                this.headerScale = 1.5;
            } else if (deltaState.header_style === 'heading3') {
                this.headerScale = 1.2;
            } else if (deltaState.header_style === 'text') {
                this.headerScale = 1;
            } else {
                this.headerScale = deltaState.header_style.fontSize;
            }

            // Adapt the header's padding
            let cssPadding = `${HEADER_PADDING * this.headerScale}rem`;
            this.headerElement.style.padding = cssPadding;

            // Make the arrow match
            let arrowSize = this.headerScale * 1.0;
            this.arrowElement.style.width = `${arrowSize}rem`;
            this.arrowElement.style.height = `${arrowSize}rem`;
            this.arrowElement.style.color = this.labelElement.style.color;
        }

        // Expand / collapse
        if (deltaState.is_open !== undefined) {
            // If this is the first state update, initialize the open fraction
            if (this.openFractionBeforeEase === -1) {
                this.openFractionBeforeEase = deltaState.is_open ? 1 : 0;
            }
            // Otherwise animate
            else {
                this.state.is_open = deltaState.is_open;
                this.startAnimationIfNotRunning();
            }

            // Update the CSS
            if (this.state.is_open) {
                this.element.classList.add('rio-revealer-open');
            } else {
                this.element.classList.remove('rio-revealer-open');
            }
        }
    }

    /// If the animation is not yet running, start it. Does nothing otherwise.
    /// This does not modify the state in any way.
    startAnimationIfNotRunning() {
        // If the animation is already running, do nothing.
        if (this.animationIsRunning) {
            return;
        }

        // Start the animation
        this.animationIsRunning = true;
        this.lastAnimationTick = Date.now();
        requestAnimationFrame(() => this.animationWorker());
    }

    animationWorker() {
        // Update state
        let now = Date.now();
        let timePassed = now - this.lastAnimationTick;
        this.lastAnimationTick = now;

        let direction = this.state.is_open ? 1 : -1;
        this.openFractionBeforeEase =
            this.openFractionBeforeEase + (direction * timePassed) / 200;

        // Clamp the open fraction
        this.openFractionBeforeEase = Math.max(
            0,
            Math.min(1, this.openFractionBeforeEase)
        );

        // If the animation is not yet finished, continue it.
        let target = this.state.is_open ? 1 : 0;
        if (this.openFractionBeforeEase === target) {
            this.animationIsRunning = false;
        } else {
            requestAnimationFrame(() => this.animationWorker());
        }
    }
}
