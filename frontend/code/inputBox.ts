import { markEventAsHandled, stopPropagation } from './eventHandling';

/// A text input field providing the following features and more:
///
/// - A floating label
/// - prefix text
/// - suffix text
export class InputBox {
    private element: HTMLElement;

    private prefixTextElement: HTMLElement;
    private suffixElementContainer: HTMLElement;
    private suffixTextElement: HTMLElement;

    private labelWidthReserverElement: HTMLElement; // Ensures enough width for the label
    private labelElement: HTMLElement;
    private _inputElement: HTMLInputElement;

    constructor(parentElement: Element) {
        this.element = document.createElement('div');
        this.element.classList.add('rio-input-box');
        parentElement.appendChild(this.element);

        this.element.innerHTML = `
        <div class="rio-input-box-hint-text rio-input-box-prefix-text"></div>
        <div class="rio-input-box-column">
            <div class="rio-input-box-label-width-reserver"></div>
            <div class="rio-input-box-label"></div>
            <input type="text">
        </div>
        <div class="rio-input-box-suffix-element">
            <div class="rio-single-container"></div>
        </div>
        <div class="rio-input-box-hint-text rio-input-box-suffix-text"></div>
        <div class="rio-input-box-plain-bar"></div>
        <div class="rio-input-box-color-bar"></div>
        `;

        this.prefixTextElement = this.element.querySelector(
            '.rio-input-box-prefix-text'
        ) as HTMLElement;
        this.suffixElementContainer = this.element.querySelector(
            '.rio-input-box-suffix-element > *'
        ) as HTMLElement;
        this.suffixTextElement = this.element.querySelector(
            '.rio-input-box-suffix-text'
        ) as HTMLElement;

        this.labelWidthReserverElement = this.element.querySelector(
            '.rio-input-box-label-width-reserver'
        ) as HTMLElement;
        this.labelElement = this.element.querySelector(
            '.rio-input-box-label'
        ) as HTMLElement;
        this._inputElement = this.element.querySelector(
            'input'
        ) as HTMLInputElement;

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
        let selectStart = (event: Event) => {
            this._inputElement.focus();
            this._inputElement.setSelectionRange(0, 0);
            markEventAsHandled(event);
        };
        this.prefixTextElement.addEventListener('click', selectStart);

        let selectEnd = (event: Event) => {
            this._inputElement.focus();
            this._inputElement.setSelectionRange(
                this._inputElement.value.length,
                this._inputElement.value.length
            );
            markEventAsHandled(event);
        };

        this.suffixElementContainer.addEventListener('click', selectEnd);
        this.suffixTextElement.addEventListener('click', selectEnd);

        // Mousedown selects the input element and/or text in it (via dragging),
        // so let it do its default behavior but then stop it from propagating
        // to other elements
        this._inputElement.addEventListener('mousedown', stopPropagation);

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
