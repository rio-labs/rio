import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';

export type SwitchState = ComponentState & {
    _type_: 'Switch-builtin';
    is_on?: boolean;
    is_sensitive?: boolean;
};

export class SwitchComponent extends ComponentBase {
    state: Required<SwitchState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-switch');

        let containerElement = document.createElement('div');
        element.appendChild(containerElement);

        let checkboxElement = document.createElement('input');
        checkboxElement.type = 'checkbox';
        containerElement.appendChild(checkboxElement);

        let knobElement = document.createElement('div');
        knobElement.classList.add('knob');
        containerElement.appendChild(knobElement);

        checkboxElement.addEventListener('change', () => {
            this.setStateAndNotifyBackend({
                is_on: checkboxElement.checked,
            });
        });

        return element;
    }

    updateElement(
        deltaState: SwitchState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.is_on !== undefined) {
            if (deltaState.is_on) {
                this.element.classList.add('is-on');
            } else {
                this.element.classList.remove('is-on');
            }

            // Assign the new value to the checkbox element, but only if it
            // differs from the current value, to avoid immediately triggering
            // the event again.
            let checkboxElement = this.element.querySelector('input');
            if (checkboxElement?.checked !== deltaState.is_on) {
                checkboxElement!.checked = deltaState.is_on;
            }
        }

        if (deltaState.is_sensitive === true) {
            this.element.classList.remove('rio-switcheroo-disabled');
            let checkbox = this.element.querySelector('input');
            checkbox!.disabled = false;
        } else if (deltaState.is_sensitive === false) {
            this.element.classList.add('rio-switcheroo-disabled');
            let checkbox = this.element.querySelector('input');
            checkbox!.disabled = true;
        }

        // TODO: The off state and the insensitive state currently look
        // identical. Make them look different. The switch animation also kinda
        // reacts to user input even if not sensitive.
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 3.18;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 1.54;
    }
}
