import { ComponentBase, ComponentState } from './componentBase';
import { getTextDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
import {
    HORIZONTAL_PADDING as INPUT_BOX_HORIZONTAL_PADDING,
    updateInputBoxNaturalHeight,
    updateInputBoxNaturalWidth,
} from '../inputBoxTools';

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

    private prefixTextWidth: number = 0;
    private suffixTextWidth: number = 0;

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

        // Detect value changes and send them to the backend
        this.inputElement = element.querySelector('input') as HTMLInputElement;

        this.inputElement.addEventListener('blur', () => {
            this.setStateAndNotifyBackend({
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
                this.state.text = this.inputElement.value;
                this.sendMessageToBackend({
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
        if (deltaState.text !== undefined) {
            this.inputElement.value = deltaState.text;
        }

        if (deltaState.label !== undefined) {
            this.labelElement.textContent = deltaState.label;

            // Update the layout
            updateInputBoxNaturalHeight(this, deltaState.label, 0);
        }

        if (deltaState.prefix_text === '') {
            this.prefixTextElement.style.display = 'none';
            this.prefixTextWidth = 0;
            this.inputElement.style.paddingLeft = `${INPUT_BOX_HORIZONTAL_PADDING}rem`;
            this.makeLayoutDirty();
        } else if (deltaState.prefix_text !== undefined) {
            this.prefixTextElement.textContent = deltaState.prefix_text;
            this.prefixTextElement.style.removeProperty('display');
            this.inputElement.style.removeProperty('padding-left');

            // Update the layout, if needed
            this.prefixTextWidth =
                getTextDimensions(deltaState.prefix_text, 'text')[0] + 0.2;
            this.makeLayoutDirty();
        }

        if (deltaState.suffix_text === '') {
            this.suffixTextElement.style.display = 'none';
            this.suffixTextWidth = 0;
            this.inputElement.style.paddingRight = `${INPUT_BOX_HORIZONTAL_PADDING}rem`;
            this.makeLayoutDirty();
        } else if (deltaState.suffix_text !== undefined) {
            this.suffixTextElement.textContent = deltaState.suffix_text;
            this.suffixTextElement.style.removeProperty('display');
            this.inputElement.style.removeProperty('padding-right');

            // Update the layout, if needed
            this.suffixTextWidth =
                getTextDimensions(deltaState.suffix_text, 'text')[0] + 0.2;
            this.makeLayoutDirty();
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

    updateNaturalWidth(ctx: LayoutContext): void {
        updateInputBoxNaturalWidth(
            this,
            this.prefixTextWidth + this.suffixTextWidth
        );
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // This is set during the updateElement() call, so there is nothing to
        // do here.
    }
}
