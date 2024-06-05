import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { PopupManager } from '../popupManager';

export type TooltipState = ComponentState & {
    _type_: 'Tooltip-builtin';
    anchor?: ComponentId;
    _tip_component?: ComponentId | null;
    position?: 'left' | 'top' | 'right' | 'bottom';
    gap?: number;
};

export class TooltipComponent extends ComponentBase {
    state: Required<TooltipState>;

    private anchorContainer: HTMLElement;
    private labelElement: HTMLElement;

    private popupManager: PopupManager;

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
            this.popupManager.setOpen(true);
        });

        this.anchorContainer.addEventListener('mouseout', () => {
            this.popupManager.setOpen(false);
        });

        // Initialize the popup manager. Many of these values will be
        // overwritten by the updateElement method.
        this.popupManager = new PopupManager(
            this.anchorContainer,
            this.labelElement,
            'center',
            0.5,
            0.0
        );

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
            this.popupManager.position = deltaState.position;
        }

        // Gap
        if (deltaState.gap !== undefined) {
            this.popupManager.gap = deltaState.gap;
        }
    }

    onDestruction(): void {
        super.onDestruction();

        this.popupManager.destroy();
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = componentsById[this.state.anchor!]!.requestedWidth;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        let anchor = componentsById[this.state.anchor!]!;
        let tip = componentsById[this.state._tip_component!]!;

        anchor.allocatedWidth = this.allocatedWidth;
        tip.allocatedWidth = tip.requestedWidth;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight =
            componentsById[this.state.anchor!]!.requestedHeight;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        let anchor = componentsById[this.state.anchor!]!;
        let tip = componentsById[this.state._tip_component!]!;

        anchor.allocatedHeight = this.allocatedHeight;
        tip.allocatedHeight = tip.requestedHeight;

        // Position the children
        anchor.element.style.left = '0';
        anchor.element.style.top = '0';

        tip.element.style.left = '0';
        tip.element.style.top = '0';
    }
}
