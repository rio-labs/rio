import { markEventAsHandled, stopPropagation } from "./eventHandling";

export type InputBoxStyle = "underlined" | "rounded" | "pill";

/// A text input field providing the following features and more:
///
/// - A floating label
/// - prefix text
/// - suffix text
export class InputBox {
    public outerElement: HTMLElement;

    private prefixTextElement: HTMLElement;
    private suffixElementContainer: HTMLElement;
    private suffixTextElement: HTMLElement;

    private labelWidthReserverElement: HTMLElement; // Ensures enough width for the label
    private labelElement: HTMLElement;

    private _accessibilityLabel: string | null;

    // NOTE: The input element can also be a textarea, but for some reason the
    // typing gets really wonky if this is a union. I don't like it, but I think
    // lying about the type is our best option.
    private _inputElement: HTMLInputElement;

    constructor({
        inputElement = undefined,
        labelIsAlwaysSmall = false,
        connectClickHandlers = true,
    }: {
        inputElement?: HTMLInputElement | HTMLTextAreaElement;
        labelIsAlwaysSmall?: boolean;
        connectClickHandlers?: boolean;
    } = {}) {
        this.outerElement = document.createElement("div");
        this.outerElement.classList.add(
            "rio-input-box",
            "rio-input-box-style-underlined"
        );

        this.outerElement.innerHTML = `
        <div class="rio-input-box-padding"></div>
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
        <div class="rio-input-box-padding"></div>
        <div class="rio-input-box-plain-bar"></div>
        <div class="rio-input-box-color-bar"></div>
        `;

        this.prefixTextElement = this.outerElement.querySelector(
            ".rio-input-box-prefix-text"
        ) as HTMLElement;
        this.suffixElementContainer = this.outerElement.querySelector(
            ".rio-input-box-suffix-element > *"
        ) as HTMLElement;
        this.suffixTextElement = this.outerElement.querySelector(
            ".rio-input-box-suffix-text"
        ) as HTMLElement;

        this.labelWidthReserverElement = this.outerElement.querySelector(
            ".rio-input-box-label-width-reserver"
        ) as HTMLElement;
        this.labelElement = this.outerElement.querySelector(
            ".rio-input-box-label"
        ) as HTMLElement;
        this._inputElement = this.outerElement.querySelector(
            "input"
        ) as HTMLInputElement;

        if (inputElement !== undefined) {
            this._inputElement.parentElement!.insertBefore(
                inputElement,
                this._inputElement
            );
            this._inputElement.remove();
            this._inputElement = inputElement as HTMLInputElement;
        }

        if (labelIsAlwaysSmall) {
            this.outerElement.classList.add("label-is-always-small");
        }

        if (connectClickHandlers) {
            this.connectClickHandlers();
        }

        // Eat keyboard events that have an effect on the input field.
        //
        // Note: It's important that we use `keydown` and not `keypress`,
        // because `KeyEventListener` doesn't have a `keypress` event and uses
        // `keydown` instead. If we use `keypress`, then the `keydown` will
        // bubble up to a parent `KeyEventListener` and be `preventDefault()`ed
        // there, which means that the user can't type.
        this._inputElement.addEventListener(
            "keydown",
            (event: KeyboardEvent) => {
                if (this._hasDefaultHandler(event)) {
                    // Don't `.preventDefault()` because then the user can't type
                    stopPropagation(event);
                }
            }
        );

        // When keyboard focus is lost, check if the input is empty so that the
        // floating label can position itself accordingly
        this._inputElement.addEventListener("blur", () => {
            if (this._inputElement.value) {
                this.outerElement.classList.add("has-value");
            } else {
                this.outerElement.classList.remove("has-value");
            }
        });

        // Assign defaults
        this.prefixText = null;
        this.suffixText = null;
        this.label = null;
    }

    private connectClickHandlers(): void {
        // Eat click events so the element can't be clicked-through
        this.outerElement.addEventListener("click", (event) => {
            stopPropagation(event);

            // Select the HTML text input
            this.focus();
        });

        this.outerElement.addEventListener("pointerdown", stopPropagation);
        this.outerElement.addEventListener("pointerup", stopPropagation);

        // Consider any clicks on the input box as handled. This prevents e.g.
        // drag events when trying to select something.
        this.prefixTextElement.addEventListener(
            "pointerdown",
            markEventAsHandled
        );
        this.suffixElementContainer.addEventListener(
            "pointerdown",
            markEventAsHandled
        );

        // When clicked, focus the text element and move the cursor accordingly.
        let selectStart = (event: Event) => {
            this._inputElement.focus();
            this._inputElement.setSelectionRange(0, 0);
            markEventAsHandled(event);
        };
        this.suffixElementContainer;
        this.prefixTextElement.addEventListener("click", selectStart);

        let selectEnd = (event: Event) => {
            this._inputElement.focus();
            this._inputElement.setSelectionRange(
                this._inputElement.value.length,
                this._inputElement.value.length
            );
            markEventAsHandled(event);
        };
        this.suffixElementContainer.addEventListener("click", selectEnd);
        this.suffixTextElement.addEventListener("click", selectEnd);

        let [paddingLeft, paddingRight] = this.outerElement.querySelectorAll(
            ".rio-input-box-padding"
        );
        paddingLeft.addEventListener("click", selectStart);
        paddingRight.addEventListener("click", selectEnd);

        // Pointer down events select the input element and/or text in it (via
        // dragging), so let them do their default behavior but then stop them
        // from propagating to other elements
        this._inputElement.addEventListener("pointerdown", stopPropagation);
    }

    private _hasDefaultHandler(event: KeyboardEvent): boolean {
        // Letters are simply inputted into the text field
        if (event.key.length === 1) {
            return true;
        }

        if (
            [
                "Backspace",
                "Delete",
                "Home",
                "End",
                "Tab",
                "ArrowLeft",
                "ArrowRight",
            ].includes(event.key)
        ) {
            return true;
        }

        if (
            (event.ctrlKey || event.metaKey) &&
            ["a", "c", "x", "v", "z", "y"].includes(event.key)
        ) {
            return true;
        }

        // Multi-line inputs have some extra hotkeys
        if (
            this._inputElement.tagName === "TEXTAREA" &&
            ["ArrowUp", "ArrowDown", "Enter"].includes(event.key)
        ) {
            return true;
        }

        return false;
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
            this.outerElement.classList.add("has-value");
        } else {
            this.outerElement.classList.remove("has-value");
        }
    }

    get label(): string | null {
        return this.labelElement.textContent;
    }

    set label(label: string | null) {
        this.labelElement.textContent = label;
        this.labelWidthReserverElement.textContent = label;

        if (label) {
            this.outerElement.classList.add("has-label");
        } else {
            this.outerElement.classList.remove("has-label");
        }

        this.updateAccessibilityLabel();
    }

    set accessibilityLabel(accessibilityLabel: string | null) {
        this._accessibilityLabel = accessibilityLabel;

        this.updateAccessibilityLabel();
    }

    private updateAccessibilityLabel(): void {
        this.inputElement.ariaLabel = this._accessibilityLabel
            ? this._accessibilityLabel
            : this.label;
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

    set style(style: InputBoxStyle) {
        this.outerElement.classList.remove(
            "rio-input-box-style-underlined",
            "rio-input-box-style-rounded",
            "rio-input-box-style-pill"
        );

        this.outerElement.classList.add(`rio-input-box-style-${style}`);
    }

    get isSensitive(): boolean {
        return !this._inputElement.disabled;
    }

    set isSensitive(isSensitive: boolean) {
        this._inputElement.disabled = !isSensitive;
        this.outerElement.classList.toggle("rio-disabled-input", !isSensitive);
    }

    set isValid(isValid: boolean) {
        if (isValid) {
            this.outerElement.style.removeProperty("--rio-local-text-color");
        } else {
            this.outerElement.style.setProperty(
                "--rio-local-text-color",
                "var(--rio-global-danger-bg)"
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
