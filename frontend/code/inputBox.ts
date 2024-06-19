/// A text input field providing the following features and more:
///
/// - A floating label
/// - prefix text

import { markEventAsHandled } from './eventHandling';

/// - suffix text
export class InputBox {
    private element: HTMLElement;

    private prefixTextElement: HTMLElement;
    private columnElement: HTMLElement;
    private suffixElementContainer: HTMLElement;
    private suffixTextElement: HTMLElement;

    private labelWidthReserverElement: HTMLElement; // Ensures enough width for the label
    private labelElement: HTMLElement;
    private _inputElement: HTMLInputElement;

    constructor(parentElement: Element) {
        this.element = document.createElement('div');
        this.element.classList.add('rio-input-box');

        // Children of `this.element`
        this.prefixTextElement = document.createElement('div');
        this.prefixTextElement.classList.add(
            'rio-input-box-hint-text',
            'rio-input-box-prefix-text'
        );
        this.element.appendChild(this.prefixTextElement);

        this.columnElement = document.createElement('div');
        this.columnElement.classList.add('rio-input-box-column');
        this.element.appendChild(this.columnElement);

        this.suffixElementContainer = document.createElement('div');
        this.suffixElementContainer.classList.add('rio-single-container');
        this.element.appendChild(this.suffixElementContainer);

        this.suffixTextElement = document.createElement('div');
        this.suffixTextElement.classList.add(
            'rio-input-box-hint-text',
            'rio-input-box-suffix-text'
        );
        this.element.appendChild(this.suffixTextElement);

        let plainBar = document.createElement('div');
        plainBar.classList.add('rio-input-box-plain-bar');
        this.element.appendChild(plainBar);

        let colorBar = document.createElement('div');
        colorBar.classList.add('rio-input-box-color-bar');
        this.element.appendChild(colorBar);

        // Children of `this.columnElement`
        this.labelWidthReserverElement = document.createElement('div');
        this.labelWidthReserverElement.classList.add(
            'rio-input-box-label-width-reserver'
        );
        this.columnElement.appendChild(this.labelWidthReserverElement);

        this.labelElement = document.createElement('div');
        this.labelElement.classList.add('rio-input-box-label');
        this.columnElement.appendChild(this.labelElement);

        this._inputElement = document.createElement('input');
        this._inputElement.type = 'text';
        this.columnElement.appendChild(this._inputElement);

        parentElement.appendChild(this.element);

        // Detect clicks on any part of the component and focus the input
        //
        // The `mousedown` are needed to prevent any potential drag events from
        // starting.
        this.prefixTextElement.addEventListener(
            'mousedown',
            markEventAsHandled
        );
        this.suffixTextElement.addEventListener(
            'mousedown',
            markEventAsHandled
        );

        // The `click` events pass focus to the input and move the cursor.
        // This has to be done in `mouseup`, rather than `mousedown`, because
        // otherwise the browser removes the focus again on mouseup.
        this.prefixTextElement.addEventListener('click', (event) => {
            this._inputElement.focus();
            this._inputElement.setSelectionRange(0, 0);
            markEventAsHandled(event);
        });

        this.suffixTextElement.addEventListener('click', (event) => {
            this._inputElement.focus();
            this._inputElement.setSelectionRange(
                this._inputElement.value.length,
                this._inputElement.value.length
            );
            markEventAsHandled(event);
        });

        // Override mousedown and eat the event so other components don't get it
        this._inputElement.addEventListener('mousedown', (event) => {
            markEventAsHandled(event);
            this._inputElement.focus();
        });

        // When keyboard focus is lost, check if the input is empty so that the
        // floating label can position itself accordingly
        this._inputElement.addEventListener('blur', () => {
            if (this._inputElement.value) {
                this.element.classList.add('has-value');
            } else {
                this.element.classList.remove('has-value');
            }
        });

        // Assign defaults
        this.prefixText = null;
        this.suffixText = null;
        this.label = null;
    }

    get inputElement(): HTMLInputElement {
        return this._inputElement;
    }

    get value(): string {
        return this._inputElement.value;
    }

    set value(value: string) {
        this._inputElement.value = value;

        if (value) {
            this.element.classList.add('has-value');
        } else {
            this.element.classList.remove('has-value');
        }
    }

    get label(): string | null {
        return this.labelElement.textContent;
    }

    set label(label: string | null) {
        this.labelElement.textContent = label;
        this.labelWidthReserverElement.textContent = label;

        if (label) {
            this.element.classList.add('has-label');
        } else {
            this.element.classList.remove('has-label');
        }
    }

    get prefixText(): string | null {
        return this.prefixTextElement.textContent;
    }

    set prefixText(prefixText: string | null) {
        this.prefixTextElement.textContent = prefixText;
    }

    get suffixText(): string | null {
        return this.suffixTextElement.textContent;
    }

    set suffixText(suffixText: string | null) {
        this.suffixTextElement.textContent = suffixText;
    }

    get suffixElement(): HTMLElement | null {
        // @ts-ignore
        return this.suffixElementContainer.firstChild;
    }

    set suffixElement(suffixElement: HTMLElement | null) {
        this.suffixElementContainer.firstChild?.remove();

        if (suffixElement !== null) {
            this.suffixElementContainer.appendChild(suffixElement);
        }
    }

    get isSensitive(): boolean {
        return !this._inputElement.disabled;
    }

    set isSensitive(isSensitive: boolean) {
        this._inputElement.disabled = !isSensitive;

        if (isSensitive) {
            this._inputElement.classList.remove('rio-disabled-input');
        } else {
            this._inputElement.classList.add('rio-disabled-input');
        }
    }

    set isValid(isValid: boolean) {
        if (isValid) {
            this.element.style.removeProperty('--rio-local-text-color');
        } else {
            this.element.style.setProperty(
                '--rio-local-text-color',
                'var(--rio-global-danger-bg)'
            );
        }
    }

    public focus(): void {
        this._inputElement.focus();
    }

    public unfocus(): void {
        this._inputElement.blur();
    }
}
