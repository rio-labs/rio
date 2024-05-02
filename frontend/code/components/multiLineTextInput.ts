import { ComponentBase, ComponentState } from './componentBase';
import { LayoutContext } from '../layouting';
import {
    updateInputBoxNaturalHeight,
    updateInputBoxNaturalWidth,
} from '../inputBoxTools';

export type MultiLineTextInputState = ComponentState & {
    _type_: 'MultiLineTextInput-builtin';
    text?: string;
    label?: string;
    is_sensitive?: boolean;
    is_valid?: boolean;
};

export class MultiLineTextInputComponent extends ComponentBase {
    state: Required<MultiLineTextInputState>;

    private labelElement: HTMLElement;
    private inputElement: HTMLTextAreaElement;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-text-input', 'rio-input-box');

        element.innerHTML = `
            <textarea placeholder=""></textarea>
            <div class="rio-input-box-label"></div>
            <div class="rio-input-box-plain-bar"></div>
            <div class="rio-input-box-color-bar"></div>
        `;

        this.labelElement = element.querySelector(
            '.rio-input-box-label'
        ) as HTMLElement;

        // Detect value changes and send them to the backend
        this.inputElement = element.querySelector(
            'textarea'
        ) as HTMLTextAreaElement;

        this.inputElement.addEventListener('blur', () => {
            this.setStateAndNotifyBackend({
                text: this.inputElement.value,
            });
        });

        // Detect shift+enter key and send it to the backend
        //
        // In addition to notifying the backend, also include the input's
        // current value. This ensures any event handlers actually use the up-to
        // date value.
        this.inputElement.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && event.shiftKey) {
                this.state.text = this.inputElement.value;
                this.sendMessageToBackend({
                    text: this.state.text,
                });

                event.preventDefault();
            }

            event.stopPropagation();
        });

        // Eat the event so other components don't get it
        this.inputElement.addEventListener('mousedown', (event) => {
            event.stopPropagation();
        });

        // The input element doesn't take up the full height of the component.
        // Catch clicks above and also make them focus the input element.
        element.addEventListener('click', (event) => {
            this.inputElement.focus();
            event.stopPropagation();
        });

        return element;
    }

    updateElement(
        deltaState: MultiLineTextInputState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.text !== undefined) {
            this.inputElement.value = deltaState.text;
        }

        if (deltaState.label !== undefined) {
            this.labelElement.textContent = deltaState.label;

            // Update the layout
            updateInputBoxNaturalHeight(this, deltaState.label, 0);
        }

        if (deltaState.is_sensitive === true) {
            this.inputElement.disabled = false;
            this.element.classList.remove('rio-disabled-input');
        } else if (deltaState.is_sensitive === false) {
            this.inputElement.disabled = true;
            this.element.classList.add('rio-disabled-input');
        }

        if (deltaState.is_valid === false) {
            this.element.style.setProperty(
                '--rio-local-text-color',
                'var(--rio-global-danger-bg)'
            );
        } else if (deltaState.is_valid === true) {
            this.element.style.removeProperty('--rio-local-text-color');
        }
    }

    grabKeyboardFocus(): void {
        this.inputElement.focus();
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        updateInputBoxNaturalWidth(this, 0);
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // This is set during the updateElement() call, so there is nothing to
        // do here.
    }
}
