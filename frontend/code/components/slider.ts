import { pixelsPerRem } from '../app';
import { LayoutContext } from '../layouting';
import { firstDefined } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';
import { MDCSlider } from '@material/slider';

export type SliderState = ComponentState & {
    _type_: 'Slider-builtin';
    minimum?: number;
    maximum?: number;
    value?: number;
    step_size?: number;
    is_sensitive?: boolean;
};

export class SliderComponent extends ComponentBase {
    state: Required<SliderState>;
    private mdcSlider: MDCSlider;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        return element;
    }

    private onSliderChange(event: Event): void {
        let value = this.mdcSlider.getValue();

        if (value !== this.state.value) {
            this.setStateAndNotifyBackend({
                value: value,
            });
        }
    }

    updateElement(
        deltaState: SliderState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (
            deltaState.minimum !== undefined ||
            deltaState.maximum !== undefined ||
            deltaState.step_size !== undefined
        ) {
            let min = firstDefined(deltaState.minimum, this.state.minimum);
            let max = firstDefined(deltaState.maximum, this.state.maximum);
            let step = firstDefined(deltaState.step_size, this.state.step_size);
            step = step == 0 ? 0.0001 : step;
            let value = firstDefined(deltaState.value, this.state.value);

            // the MDC slider contains margin. If Rio explicitly sets the
            // component's width, that makes the slider exceed its boundaries.
            // Thus, contain it in a sub-div.
            this.element.innerHTML = `
            <div class="mdc-slider" style="pointer-events: auto">
                <input class="mdc-slider__input" type="range" min="${min}" max="${max}" value="${value}" step="${step}">
                <div class="mdc-slider__track">
                    <div class="mdc-slider__track--inactive"></div>
                    <div class="mdc-slider__track--active">
                        <div class="mdc-slider__track--active_fill"></div>
                    </div>
                </div>
                <div class="mdc-slider__thumb">
                    <div class="mdc-slider__thumb-knob"></div>
                </div>
            </div>
            `;

            // Initialize the material design component
            this.mdcSlider = new MDCSlider(
                this.element.firstElementChild as HTMLElement
            );

            // Subscribe to changes
            this.mdcSlider.listen(
                'MDCSlider:change',
                this.onSliderChange.bind(this)
            );
        }

        if (deltaState.value !== undefined) {
            let value = deltaState.value;

            // The server can send invalid values due to reconciliation. Fix
            // them.
            value = Math.max(
                value,
                firstDefined(deltaState.minimum, this.state.minimum)
            );
            value = Math.min(
                value,
                firstDefined(deltaState.maximum, this.state.maximum)
            );

            let step = firstDefined(deltaState.step_size, this.state.step_size);
            step = step == 0 ? 0.0001 : step;
            value = Math.round(value / step) * step;
        }

        if (deltaState.is_sensitive !== undefined) {
            this.mdcSlider.setDisabled(!deltaState.is_sensitive);
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 6;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // The MDC slider component is hardcoded at 48px height.
        this.naturalHeight = 48 / pixelsPerRem;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // The slider stores the coordinates of its rectangle. Since rio
        // likes to resize and move around components, the rectangle must be
        // updated appropriately.
        //
        // Really, this should be done when the component is resized or moved, but
        // there is no hook for that. Update seems to work fine for now.
        this.mdcSlider.layout();
    }
}
