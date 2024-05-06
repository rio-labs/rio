import { applySwitcheroo } from '../designApplication';
import { ColorSet, ComponentId } from '../dataModels';
import { RippleEffect } from '../rippleEffect';
import { ComponentBase, ComponentState } from './componentBase';
import { SingleContainer } from './singleContainer';

export type CardState = ComponentState & {
    _type_: 'Card-builtin';
    content?: ComponentId;
    corner_radius?: number | [number, number, number, number];
    reportPress?: boolean;
    ripple?: boolean;
    elevate_on_hover?: boolean;
    colorize_on_hover?: boolean;
    color?: ColorSet;
};

export class CardComponent extends SingleContainer {
    state: Required<CardState>;

    // If this card has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-card');

        // Detect presses
        element.onclick = (event) => {
            // Is the backend interested in presses?
            if (!this.state.reportPress) {
                return;
            }

            // The event was handled. Stop it from propagating further.
            event.stopPropagation();

            // Notify the backend
            this.sendMessageToBackend({});
        };

        return element;
    }

    updateElement(
        deltaState: CardState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the child
        this.replaceOnlyChild(latentComponents, deltaState.content);

        // Update the corner radius
        if (deltaState.corner_radius !== undefined) {
            if (typeof deltaState.corner_radius === 'number') {
                this.element.style.borderRadius = `${deltaState.corner_radius}rem`;
            } else {
                this.element.style.borderRadius = `${deltaState.corner_radius[0]}rem ${deltaState.corner_radius[1]}rem ${deltaState.corner_radius[2]}rem ${deltaState.corner_radius[3]}rem`;
            }
        }

        // Report presses?
        if (deltaState.reportPress === true) {
            this.element.style.cursor = 'pointer';
        } else if (deltaState.reportPress === false) {
            this.element.style.removeProperty('cursor');
        }

        // Ripple
        if (deltaState.ripple === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(this.element);

                this.element.classList.add('rio-card-ripple');
            }
        } else if (deltaState.ripple === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;

                this.element.classList.remove('rio-card-ripple');
            }
        }

        // Elevate on hover
        if (deltaState.elevate_on_hover === true) {
            this.element.classList.add('rio-card-elevate-on-hover');
        } else if (deltaState.elevate_on_hover === false) {
            this.element.classList.remove('rio-card-elevate-on-hover');
        }

        // Colorize on hover
        if (deltaState.colorize_on_hover === true) {
            this.element.classList.add('rio-card-colorize-on-hover');
        } else if (deltaState.colorize_on_hover === false) {
            this.element.classList.remove('rio-card-colorize-on-hover');
        }

        // Colorize
        if (deltaState.color !== undefined) {
            applySwitcheroo(this.element, deltaState.color);
        }
    }
}
