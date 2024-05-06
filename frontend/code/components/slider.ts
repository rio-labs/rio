import { pixelsPerRem } from '../app';
import { applySwitcheroo } from '../designApplication';
import { LayoutContext } from '../layouting';
import { firstDefined } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';

export type SliderState = ComponentState & {
    _type_: 'Slider-builtin';
    minimum?: number;
    maximum?: number;
    value?: number;
    step?: number;
    is_sensitive?: boolean;
    ticks?: (number | string | [number, string])[] | boolean;
};

export class SliderComponent extends ComponentBase {
    state: Required<SliderState>;

    private innerElement: HTMLElement;

    createElement(): HTMLElement {
        // Create the HTML structure
        let element = document.createElement('div');
        element.classList.add('rio-slider');
        element.innerHTML = `
            <div class="rio-slider-inner">
                <div class="rio-slider-track"></div>
                <div class="rio-slider-fill"></div>
                <div class="rio-slider-glow"></div>
                <div class="rio-slider-knob"></div>
            </div>
        `;

        // Expose the elements
        this.innerElement = element.querySelector(
            '.rio-slider-inner'
        ) as HTMLElement;

        // Subscribe to events
        this.addDragHandler({
            element: element,
            onStart: this.onDragStart.bind(this),
            onMove: this.onDragMove.bind(this),
            onEnd: this.onDragEnd.bind(this),
        });

        return element;
    }

    private setValueFromMouseEvent(event: MouseEvent): number {
        // If the slider is disabled, do nothing
        if (!this.state.is_sensitive) {
            return this.state.value;
        }

        // Calculate the value as a fraction of the track width
        let rect = this.innerElement.getBoundingClientRect();
        let fraction = (event.clientX - rect.left) / rect.width;
        fraction = Math.max(0, Math.min(1, fraction));

        // Enforce the step size
        let valueRange = this.state.maximum - this.state.minimum;

        if (this.state.step !== 0) {
            let normalizedStepSize = this.state.step / valueRange;

            fraction =
                Math.round(fraction / normalizedStepSize) * normalizedStepSize;
        }

        // Move the knob
        this.innerElement.style.setProperty(
            '--rio-slider-fraction',
            `${fraction * 100}%`
        );

        // Return the new value
        return fraction * valueRange + this.state.minimum;
    }

    private onDragStart(event: MouseEvent): boolean {
        this.setValueFromMouseEvent(event);
        return true;
    }

    private onDragMove(event: MouseEvent): void {
        // Make future transitions instant to avoid lag
        this.element.style.setProperty(
            '--rio-slider-position-transition-time',
            '0s'
        );

        this.setValueFromMouseEvent(event);
    }

    private onDragEnd(event: MouseEvent): void {
        // Revert to the default transition time
        this.element.style.removeProperty(
            '--rio-slider-position-transition-time'
        );

        // Get the new value
        let value = this.setValueFromMouseEvent(event);

        // Update state and notify the backend of the new value
        this.setStateAndNotifyBackend({
            value: value,
        });
    }

    updateElement(
        deltaState: SliderState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (
            deltaState.minimum !== undefined ||
            deltaState.maximum !== undefined ||
            deltaState.step !== undefined ||
            deltaState.value !== undefined
        ) {
            // The server can send invalid values due to reconciliation. Fix
            // them.
            let value = firstDefined(deltaState.value, this.state.value);
            let step = firstDefined(deltaState.step, this.state.step);
            let minimum = firstDefined(deltaState.minimum, this.state.minimum);
            let maximum = firstDefined(deltaState.maximum, this.state.maximum);

            // Bring the value into a valid range
            value = Math.max(minimum, Math.min(maximum, value));

            // Apply the step size
            if (step !== 0) {
                value = Math.round(value / step) * step;
            }

            // Update the CSS
            let fraction = (value - minimum) / (maximum - minimum);
            this.innerElement.style.setProperty(
                '--rio-slider-fraction',
                `${fraction * 100}%`
            );
        }

        if (deltaState.is_sensitive === true) {
            applySwitcheroo(this.element, 'keep');
        } else if (deltaState.is_sensitive === false) {
            applySwitcheroo(this.element, 'disabled');
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 3;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 1.4;
    }
}
