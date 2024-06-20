import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { PopupManager } from '../popupManager';

export type TooltipState = ComponentState & {
    _type_: 'Tooltip-builtin';
    anchor?: ComponentId;
    _tip_component?: ComponentId | null;
    position?: 'auto' | 'left' | 'top' | 'right' | 'bottom';
    gap?: number;
};

export class TooltipComponent extends ComponentBase {
    state: Required<TooltipState>;

    private popupElement: HTMLElement;
    private popupManager: PopupManager;

    createElement(): HTMLElement {
        // Set up the HTML
        let element = document.createElement('div');
        element.classList.add('rio-tooltip');

        this.popupElement = document.createElement('div');
        this.popupElement.classList.add(
            'rio-tooltip-popup',
            'rio-popup-animation-scale',
            'rio-switcheroo-hud'
        );

        // Listen for events
        element.addEventListener('mouseover', () => {
            this.popupManager.isOpen = true;
        });

        element.addEventListener('mouseout', () => {
            this.popupManager.isOpen = false;
        });

        // Initialize the popup manager. Many of these values will be
        // overwritten by the updateElement method.
        this.popupManager = new PopupManager(
            element,
            this.popupElement,
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
        super.updateElement(deltaState, latentComponents);

        // Update the anchor
        if (deltaState.anchor !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.anchor,
                this.element
            );
        }

        // Update tip
        if (deltaState._tip_component !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState._tip_component,
                this.popupElement
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
}
