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
    show_values?: boolean;
    ticks?: (number | string | [number, string])[] | boolean;
};

export class SliderComponent extends ComponentBase {
    state: Required<SliderState>;

    private innerElement: HTMLElement;
    private minValueElement: HTMLElement;
    private maxValueElement: HTMLElement;
    private currentValueElement: HTMLElement;

    createElement(): HTMLElement {
        // Create the HTML structure
        let element = document.createElement('div');
        element.classList.add('rio-slider');
        element.innerHTML = `
        <div class="rio-slider-inner">
            <div class="rio-slider-track"></div>
            <div class="rio-slider-fill"></div>
            <div class="rio-slider-glow"></div>
            <div class="rio-slider-knob">
                ${this.state.show_values ? '<div class="rio-slider-current-value"></div>' : ''}
            </div>
            ${
                this.state.show_values
                    ? `
                <div class="rio-slider-values">
                    <div class="rio-slider-min-value"></div>
                    <div class="rio-slider-max-value"></div>
                </div>`
                    : ''
            }
        </div>
    `;

        // Expose the elements
        this.innerElement = element.querySelector(
            '.rio-slider-inner'
        ) as HTMLElement;
        this.currentValueElement = element.querySelector(
            '.rio-slider-current-value'
        ) as HTMLElement;
        if (this.state.show_values) {
            this.minValueElement = element.querySelector(
                '.rio-slider-min-value'
            ) as HTMLElement;
            this.maxValueElement = element.querySelector(
                '.rio-slider-max-value'
            ) as HTMLElement;
        }

        // Subscribe to events
        this.addDragHandler({
            element: element,
            onStart: this.onDragStart.bind(this),
            onMove: this.onDragMove.bind(this),
            onEnd: this.onDragEnd.bind(this),
        });

        return element;
    }

    private setValueFromMouseEvent(event: MouseEvent): [number, number] {
        // If the slider is disabled, do nothing
        if (!this.state.is_sensitive) {
            return [this.state.value, this.state.value];
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

        // Return the new value and fraction
        let newValue = fraction * valueRange + this.state.minimum;
        return [fraction, newValue];
    }

    private onDragStart(event: MouseEvent): boolean {
        event.stopPropagation();
        event.preventDefault();

        this.setValueFromMouseEvent(event);
        return true;
    }

    private onDragMove(event: MouseEvent): void {
        event.stopPropagation();
        event.preventDefault();

        // Make future transitions instant to avoid lag
        this.element.style.setProperty(
            '--rio-slider-position-transition-time',
            '0s'
        );

        const [fraction, newValue] = this.setValueFromMouseEvent(event);

        if (this.state.show_values) {
            this.currentValueElement.textContent = newValue.toFixed(2);
        }
    }

    private onDragEnd(event: MouseEvent): void {
        event.stopPropagation();
        event.preventDefault();

        // Revert to the default transition time
        this.element.style.removeProperty(
            '--rio-slider-position-transition-time'
        );

        // Get the new value
        let [fraction, value] = this.setValueFromMouseEvent(event);

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

            if (this.state.show_values) {
                this.minValueElement.textContent = minimum.toFixed(2);
                this.maxValueElement.textContent = maximum.toFixed(2);
                this.currentValueElement.textContent = value.toFixed(2);
            }
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
