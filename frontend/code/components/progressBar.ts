import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';
import { MDCLinearProgress } from '@material/linear-progress';

export type ProgressBarState = ComponentState & {
    _type_: 'ProgressBar-builtin';
    progress?: number | null;
};

export class ProgressBarComponent extends ComponentBase {
    state: Required<ProgressBarState>;
    private mdcProgress: MDCLinearProgress;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('mdc-linear-progress');
        element.setAttribute('role', 'progressbar');

        element.innerHTML = `
<div class="mdc-linear-progress__buffer">
    <div class="mdc-linear-progress__buffer-bar"></div>
    <div class="mdc-linear-progress__buffer-dots"></div>
</div>
<div class="mdc-linear-progress__bar mdc-linear-progress__primary-bar">
    <span class="mdc-linear-progress__bar-inner"></span>
</div>
<div class="mdc-linear-progress__bar mdc-linear-progress__secondary-bar">
    <span class="mdc-linear-progress__bar-inner"></span>
</div>
        `;

        // Initialize the material design component
        this.mdcProgress = new MDCLinearProgress(element);

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
            this.mdcProgress.determinate = false;
        }

        // Known progress
        else {
            this.mdcProgress.determinate = true;
            this.mdcProgress.progress = deltaState.progress;
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 3;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 0.2;
    }
}
