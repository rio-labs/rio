import { ComponentStatesUpdateContext } from "../componentManagement";
import { markEventAsHandled } from "../eventHandling";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type SliderState = ComponentState & {
    _type_: "Slider-builtin";
    minimum: number;
    maximum: number;
    value: number;
    step: number;
    is_sensitive: boolean;
    show_values: boolean;
    ticks: (number | string | [number, string])[] | boolean;
};

export class SliderComponent extends ComponentBase<SliderState> {
    private innerElement: HTMLElement;
    private minValueElement: HTMLElement;
    private maxValueElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the HTML structure
        let element = document.createElement("div");
        element.classList.add("rio-slider");
        element.role = "slider";
        element.innerHTML = `
            <div class="rio-slider-column">
                <div class="rio-slider-inner">
                    <div class="rio-slider-track"></div>
                    <div class="rio-slider-fill"></div>
                    <div class="rio-slider-glow"></div>
                    <div class="rio-slider-knob"></div>
                </div>
                <div class="rio-slider-values">
                    <div class="rio-slider-min-value"></div>
                    <div class="rio-slider-max-value"></div>
                </div>
            </div>
        `;

        // Expose the elements
        this.innerElement = element.querySelector(
            ".rio-slider-inner"
        ) as HTMLElement;

        this.minValueElement = element.querySelector(
            ".rio-slider-min-value"
        ) as HTMLElement;

        this.maxValueElement = element.querySelector(
            ".rio-slider-max-value"
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

    private setValueFromPointerEvent(event: PointerEvent): [number, number] {
        // If the slider is disabled, do nothing
        if (!this.state.is_sensitive) {
            return [this.state.value, this.state.value];
        }

        // Calculate the selected value from the event coordinates
        let rect = this.innerElement.getBoundingClientRect();
        let fraction = (event.clientX - rect.left) / rect.width;
        fraction = Math.max(0, Math.min(1, fraction));

        let valueRange = this.state.maximum - this.state.minimum;
        let value = fraction * valueRange + this.state.minimum;

        // Enforce the step size
        //
        // Converting to a value, and back to fractions may seem convoluted, but
        // this ensures that the step size is enforced correctly. Careless math
        // can lead to floating point errors that cause the reported value to be
        // off by a little (e.g. 7.99999999 instead of 8).
        if (this.state.step !== 0) {
            let stepIndex = Math.round(value / this.state.step);
            value = stepIndex * this.state.step;

            fraction = (value - this.state.minimum) / valueRange;
        }

        // Move the knob
        this.innerElement.style.setProperty(
            "--rio-slider-fraction",
            `${fraction * 100}%`
        );

        // Return the new value and fraction
        let newValue = fraction * valueRange + this.state.minimum;
        return [fraction, newValue];
    }

    private onDragStart(event: PointerEvent): boolean {
        markEventAsHandled(event);

        this.setValueFromPointerEvent(event);
        return true;
    }

    private onDragMove(event: PointerEvent): void {
        markEventAsHandled(event);

        // Make future transitions instant to avoid lag
        this.element.style.setProperty(
            "--rio-slider-position-transition-time",
            "0s"
        );

        this.setValueFromPointerEvent(event);
    }

    private onDragEnd(event: PointerEvent): void {
        markEventAsHandled(event);

        // Revert to the default transition time
        this.element.style.removeProperty(
            "--rio-slider-position-transition-time"
        );

        // Get the new value
        let [fraction, value] = this.setValueFromPointerEvent(event);

        // Update state and notify the backend of the new value
        this.setStateAndNotifyBackend({
            value: value,
        });
    }

    updateElement(
        deltaState: DeltaState<SliderState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (
            deltaState.minimum !== undefined ||
            deltaState.maximum !== undefined ||
            deltaState.step !== undefined ||
            deltaState.value !== undefined
        ) {
            // The server can send invalid values due to reconciliation. Fix
            // them.
            let value = deltaState.value ?? this.state.value;
            let step = deltaState.step ?? this.state.step;
            let minimum = deltaState.minimum ?? this.state.minimum;
            let maximum = deltaState.maximum ?? this.state.maximum;

            // Bring the value into a valid range
            value = Math.max(minimum, Math.min(maximum, value));

            // Apply the step size
            if (step !== 0) {
                value = Math.round(value / step) * step;
            }

            // Update the CSS
            let fraction = (value - minimum) / (maximum - minimum);
            this.innerElement.style.setProperty(
                "--rio-slider-fraction",
                `${fraction * 100}%`
            );

            this.minValueElement.textContent = minimum.toFixed(2);
            this.maxValueElement.textContent = maximum.toFixed(2);

            // Update accessibility properties
            this.element.ariaValueMin = minimum.toString();
            this.element.ariaValueMax = maximum.toString();
            this.element.ariaValueNow = value.toString();
        }

        if (deltaState.is_sensitive === true) {
            this.element.classList.remove("rio-disabled-input");
            this.element.ariaDisabled = "false";
        } else if (deltaState.is_sensitive === false) {
            this.element.classList.add("rio-disabled-input");
            this.element.ariaDisabled = "true";
        }

        if (deltaState.show_values === true) {
            this.minValueElement.style.display = "block";
            this.maxValueElement.style.display = "block";
        } else if (deltaState.show_values === false) {
            this.minValueElement.style.display = "none";
            this.maxValueElement.style.display = "none";
        }
    }
}
