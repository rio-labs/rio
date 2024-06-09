import { ComponentBase, ComponentState } from './componentBase';
import { Debouncer } from '../debouncer';

export type TextInputState = ComponentState & {
    _type_: 'TextInput-builtin';
    text?: string;
    label?: string;
    prefix_text?: string;
    suffix_text?: string;
    is_secret?: boolean;
    is_sensitive?: boolean;
    is_valid?: boolean;
};

export class TextInputComponent extends ComponentBase {
    state: Required<TextInputState>;

    private labelElement: HTMLElement;
    private inputElement: HTMLInputElement;
    private prefixTextElement: HTMLElement;
    private suffixTextElement: HTMLElement;

    onChangeLimiter: Debouncer;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-text-input', 'rio-input-box');

        element.innerHTML = `
            <input type="text" style="order: 2" placeholder="">
            <div class="rio-text-input-hint-text rio-text-input-prefix-text" style="order: 1"></div>
            <div class="rio-text-input-hint-text rio-text-input-suffix-text" style="order: 3"></div>
            <div class="rio-input-box-label"></div>
            <div class="rio-input-box-plain-bar"></div>
            <div class="rio-input-box-color-bar"></div>
        `;

        this.labelElement = element.querySelector(
            '.rio-input-box-label'
        ) as HTMLElement;

        [this.prefixTextElement, this.suffixTextElement] = Array.from(
            element.querySelectorAll('.rio-text-input-hint-text')
        ) as HTMLElement[];

        // Create a rate-limited function for notifying the backend of changes.
        // This allows reporting changes to the backend in real-time, rather
        // just when losing focus.
        this.onChangeLimiter = new Debouncer({
            callback: (newText: string) => {
                this._setStateDontNotifyBackend({
                    text: newText,
                });

                this.sendMessageToBackend({
                    type: 'change',
                    text: newText,
                });
            },
        });

        // Detect value changes and send them to the backend
        this.inputElement = element.querySelector('input') as HTMLInputElement;

        this.inputElement.addEventListener('input', () => {
            this.onChangeLimiter.call(this.inputElement.value);
        });

        // Detect focus gain...
        this.inputElement.addEventListener('focus', () => {
            this.sendMessageToBackend({
                type: 'gainFocus',
                text: this.inputElement.value,
            });
        });

        // ...and focus loss
        this.inputElement.addEventListener('blur', () => {
            this.onChangeLimiter.clear();

            this.sendMessageToBackend({
                type: 'loseFocus',
                text: this.inputElement.value,
            });
        });

        // Detect the enter key and send it to the backend
        //
        // In addition to notifying the backend, also include the input's
        // current value. This ensures any event handlers actually use the up-to
        // date value.
        this.inputElement.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                // Update the state
                this.state.text = this.inputElement.value;

                // There is no need for the debouncer to report this call, since
                // Python will already trigger both change & confirm events when
                // it receives the message that is about to be sent.
                this.onChangeLimiter.clear();

                // Inform the backend
                this.sendMessageToBackend({
                    type: 'confirm',
                    text: this.state.text,
                });
            }

            event.stopPropagation();
        });

        // Detect clicks on any part of the component and focus the input
        //
        // The `mousedown` are needed to prevent any potential drag events from
        // starting.
        this.prefixTextElement.addEventListener('mousedown', (event) => {
            event.stopPropagation();
        });

        this.suffixTextElement.addEventListener('mousedown', (event) => {
            event.stopPropagation();
        });

        // The `click` events pass focus to the input and move the cursor.
        // This has to be done in `mouseup`, rather than `mousedown`, because
        // otherwise the browser removes the focus again on mouseup.
        this.prefixTextElement.addEventListener('click', (event) => {
            this.inputElement.focus();
            this.inputElement.setSelectionRange(0, 0);
            event.stopPropagation();
        });

        this.suffixTextElement.addEventListener('click', (event) => {
            this.inputElement.focus();
            this.inputElement.setSelectionRange(
                this.inputElement.value.length,
                this.inputElement.value.length
            );
            event.stopPropagation();
        });

        // Eat the event so other components don't get it
        this.inputElement.addEventListener('mousedown', (event) => {
            event.stopPropagation();
        });

        return element;
    }

    updateElement(
        deltaState: TextInputState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.text !== undefined) {
            this.inputElement.value = deltaState.text;
        }

        if (deltaState.label !== undefined) {
            this.labelElement.textContent = deltaState.label;
        }

        if (deltaState.prefix_text === '') {
            this.prefixTextElement.style.display = 'none';
        } else if (deltaState.prefix_text !== undefined) {
            this.prefixTextElement.textContent = deltaState.prefix_text;
            this.prefixTextElement.style.removeProperty('display');
            this.inputElement.style.removeProperty('padding-left');
        }

        if (deltaState.suffix_text === '') {
            this.suffixTextElement.style.display = 'none';
        } else if (deltaState.suffix_text !== undefined) {
            this.suffixTextElement.textContent = deltaState.suffix_text;
            this.suffixTextElement.style.removeProperty('display');
            this.inputElement.style.removeProperty('padding-right');
        }

        if (deltaState.is_secret !== undefined) {
            this.inputElement.type = deltaState.is_secret ? 'password' : 'text';
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
}
