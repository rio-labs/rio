import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';

export type ProgressBarState = ComponentState & {
    _type_: 'ProgressBar-builtin';
    progress?: number | null;
};

export class ProgressBarComponent extends ComponentBase {
    state: Required<ProgressBarState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-progressbar');

        element.innerHTML = `
            <div class="rio-progressbar-inner">
                <div class="rio-progressbar-track"></div>
                <div class="rio-progressbar-fill"></div>
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
            this.element.classList.add('rio-progressbar-indeterminate');
        }

        // Known progress
        else {
            this.element.style.setProperty(
                '--rio-progressbar-fraction',
                `${deltaState.progress * 100}%`
            );
            this.element.classList.remove('rio-progressbar-indeterminate');
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 3;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 0.25;
    }
}
