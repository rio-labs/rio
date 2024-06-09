import { applyIcon } from '../designApplication';
import { ComponentBase, ComponentState } from './componentBase';

export type BuildFailedState = ComponentState & {
    _type_: 'BuildFailed-builtin';
    error_summary: string;
    error_details: string;
};

export class BuildFailedComponent extends ComponentBase {
    state: Required<BuildFailedState>;

    private iconElement: HTMLElement;
    private summaryElement: HTMLElement;
    private detailsElement: HTMLElement;

    createElement(): HTMLElement {
        // Create the elements
        let element = document.createElement('div');
        element.classList.add('rio-build-failed');

        element.innerHTML = `
            <div class="rio-build-failed-top"></div>
            <div class="rio-build-failed-content">
                <div class="rio-build-failed-header">
                    <div class="rio-build-failed-icon"></div>
                    <div class="rio-build-failed-summary"></div>
                </div>
                <div class="rio-build-failed-details"></div>
            </div>
            <div class="rio-build-failed-bottom"></div>
        `;

        // Expose them
        this.iconElement = element.querySelector(
            '.rio-build-failed-icon'
        ) as HTMLElement;

        this.summaryElement = element.querySelector(
            '.rio-build-failed-summary'
        ) as HTMLElement;

        this.detailsElement = element.querySelector(
            '.rio-build-failed-details'
        ) as HTMLElement;

        // And initialize them
        applyIcon(
            this.iconElement,
            'material/error:fill',
            'var(--rio-global-danger-fg)'
        );

        return element;
    }

    updateElement(
        deltaState: BuildFailedState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.error_summary !== undefined) {
            this.summaryElement.innerText = deltaState.error_summary;
        }

        if (deltaState.error_details !== undefined) {
            this.detailsElement.innerText = deltaState.error_details;
        }
    }
}
