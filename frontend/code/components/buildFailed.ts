import { applyIcon } from '../designApplication';
import { getElementDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
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
        if (deltaState.error_summary !== undefined) {
            this.summaryElement.innerText = deltaState.error_summary;
        }

        if (deltaState.error_details !== undefined) {
            this.detailsElement.innerText = deltaState.error_details;
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 4;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 4;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Display the contents based on how much space the component has
        // received
        let summaryDims = getElementDimensions(this.summaryElement);
        let detailsDims = getElementDimensions(this.detailsElement);

        let summaryVisible = this.allocatedWidth > summaryDims[0] + 6; // The padding is a guess
        let detailsVisible =
            summaryVisible &&
            this.allocatedWidth > detailsDims[0] + 1 && // The padding is a guess
            this.allocatedHeight > detailsDims[1] + 6; // The padding is a guess

        // Special case: No contents provided
        summaryVisible = summaryVisible && this.state.error_summary.length > 0;
        detailsVisible = detailsVisible && this.state.error_details.length > 0;

        // Show/hide the elements
        this.summaryElement.style.display = summaryVisible ? '' : 'none';
        this.detailsElement.style.display = detailsVisible ? '' : 'none';
    }
}
