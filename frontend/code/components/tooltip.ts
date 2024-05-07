import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type TooltipState = ComponentState & {
    _type_: 'Tooltip-builtin';
    anchor?: ComponentId;
    _tip_component?: ComponentId | null;
    position?: 'left' | 'top' | 'right' | 'bottom';
};

export class TooltipComponent extends ComponentBase {
    state: Required<TooltipState>;

    private anchorContainer: HTMLElement;
    private labelElement: HTMLElement;

    createElement(): HTMLElement {
        // Set up the HTML
        let element = document.createElement('div');
        element.classList.add('rio-tooltip');

        element.innerHTML = `
            <div class="rio-tooltip-anchor"></div>
            <div class="rio-tooltip-label rio-switcheroo-hud"></div>
        `;

        this.anchorContainer = element.querySelector(
            '.rio-tooltip-anchor'
        ) as HTMLElement;

        this.labelElement = element.querySelector(
            '.rio-tooltip-label'
        ) as HTMLElement;

        // Listen for events
        this.anchorContainer.addEventListener('mouseover', () => {
            this.labelElement.style.opacity = '1';
        });

        this.anchorContainer.addEventListener('mouseout', () => {
            this.labelElement.style.opacity = '0';
        });

        return element;
    }

    updateElement(
        deltaState: TooltipState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the anchor
        if (deltaState.anchor !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.anchor,
                this.anchorContainer
            );
        }

        // Update tip
        if (deltaState._tip_component !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState._tip_component,
                this.labelElement
            );
        }

        // Position
        if (deltaState.position !== undefined) {
            let left, top, right, bottom, transform;

            const theOne = 'calc(100% + 0.5rem)';

            if (deltaState.position === 'left') {
                left = 'unset';
                top = '50%';
                right = theOne;
                bottom = 'unset';
                transform = 'translateY(-50%)';
            } else if (deltaState.position === 'top') {
                left = '50%';
                top = 'unset';
                right = 'unset';
                bottom = theOne;
                transform = 'translateX(-50%)';
            } else if (deltaState.position === 'right') {
                left = theOne;
                top = '50%';
                right = 'unset';
                bottom = 'unset';
                transform = 'translateY(-50%)';
            } else {
                left = '50%';
                top = theOne;
                right = 'unset';
                bottom = 'unset';
                transform = 'translateX(-50%)';
            }

            this.labelElement.style.left = left;
            this.labelElement.style.top = top;
            this.labelElement.style.right = right;
            this.labelElement.style.bottom = bottom;
            this.labelElement.style.transform = transform;
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = componentsById[this.state.anchor!]!.requestedWidth;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        let anchor = componentsById[this.state.anchor!]!;
        let tip = componentsById[this.state._tip_component!]!;

        anchor.allocatedWidth = this.allocatedWidth;
        tip.allocatedWidth = tip.naturalWidth;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight =
            componentsById[this.state.anchor!]!.requestedHeight;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        let anchor = componentsById[this.state.anchor!]!;
        let tip = componentsById[this.state._tip_component!]!;

        anchor.allocatedHeight = this.allocatedHeight;
        tip.allocatedHeight = tip.naturalHeight;

        // Position the children
        anchor.element.style.left = '0';
        anchor.element.style.top = '0';

        tip.element.style.left = '0';
        tip.element.style.top = '0';
    }
}
