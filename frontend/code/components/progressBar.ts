import { ColorSet } from '../dataModels';
import { applySwitcheroo } from '../designApplication';
import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';

export type ProgressBarState = ComponentState & {
    _type_: 'ProgressBar-builtin';
    progress?: number | null;
    color?: ColorSet;
};

export class ProgressBarComponent extends ComponentBase {
    state: Required<ProgressBarState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-progress-bar');

        element.innerHTML = `
            <div class="rio-progress-bar-inner">
                <div class="rio-progress-bar-track"></div>
                <div class="rio-progress-bar-fill"></div>
            </div>
        `;

        return element;
    }

    updateElement(
        deltaState: ProgressBarState,
        latentComponents: Set<ComponentBase>
    ): void {
        // No progress specified
        if (deltaState.progress === undefined) {
        }

        // Indeterminate progress
        else if (deltaState.progress === null) {
            this.element.classList.add('rio-progress-bar-indeterminate');
        }

        // Known progress
        else {
            let progress = Math.max(0, Math.min(1, deltaState.progress));

            this.element.style.setProperty(
                '--rio-progress-bar-fraction',
                `${progress * 100}%`
            );
            this.element.classList.remove('rio-progress-bar-indeterminate');
        }

        // Apply the color
        if (deltaState.color !== undefined) {
            applySwitcheroo(
                this.element,
                deltaState.color === 'keep' ? 'bump' : deltaState.color
            );
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 3;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 0.25;
    }
}
