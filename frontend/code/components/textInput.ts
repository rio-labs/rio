import { ComponentBase, DeltaState } from "./componentBase";
import { Debouncer } from "../debouncer";
import { InputBox, InputBoxStyle } from "../inputBox";
import { markEventAsHandled, stopPropagation } from "../eventHandling";
import {
    KeyboardFocusableComponent,
    KeyboardFocusableComponentState,
} from "./keyboardFocusableComponent";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type TextInputState = KeyboardFocusableComponentState & {
    _type_: "TextInput-builtin";
    text: string;
    label: string;
    accessibility_label: string;
    style: InputBoxStyle;
    prefix_text: string;
    suffix_text: string;
    is_secret: boolean;
    is_sensitive: boolean;
    is_valid: boolean;
    reportFocusGain: boolean;
};

export class TextInputComponent extends KeyboardFocusableComponent<TextInputState> {
    private inputBox: InputBox;
    private onChangeLimiter: Debouncer;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        this.inputBox = new InputBox();

        let element = this.inputBox.outerElement;

        // Create a rate-limited function for notifying the backend of changes.
        // This allows reporting changes to the backend in real-time, rather
        // just when losing focus.
        this.onChangeLimiter = new Debouncer({
            callback: (newText: string) => {
                this.state.text = newText;

                this.sendMessageToBackend({
                    type: "change",
                    text: newText,
                });
            },
        });

        // Detect value changes and send them to the backend
        this.inputBox.inputElement.addEventListener("input", () => {
            this.onChangeLimiter.call(this.inputBox.value);
        });

        // Detect focus gain...
        this.inputBox.inputElement.addEventListener("focus", () => {
            if (this.state.reportFocusGain) {
                this.sendMessageToBackend({
                    type: "gainFocus",
                    text: this.inputBox.inputElement.value,
                });
            }
        });

        // ...and focus loss
        this.inputBox.inputElement.addEventListener("blur", () => {
            this.onChangeLimiter.clear();

            this.state.text = this.inputBox.value;

            this.sendMessageToBackend({
                type: "loseFocus",
                text: this.inputBox.value,
            });
        });

        // Detect `enter` and send them to the backend
        //
        // In addition to notifying the backend, also include the input's
        // current value. This ensures any event handlers actually use the up-to
        // date value.
        this.inputBox.inputElement.addEventListener(
            "keydown",
            (event) => {
                if (event.key === "Enter") {
                    // Update the state
                    this.state.text = this.inputBox.value;

                    // There is no need for the debouncer to report this call,
                    // since Python will already trigger both change & confirm
                    // events when it receives the message that is about to be
                    // sent.
                    this.onChangeLimiter.clear();

                    // Inform the backend
                    this.sendMessageToBackend({
                        type: "confirm",
                        text: this.state.text,
                    });

                    markEventAsHandled(event);
                }
            },
            { capture: true }
        );

        return element;
    }

    updateElement(
        deltaState: DeltaState<TextInputState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.text !== undefined) {
            this.inputBox.value = deltaState.text;
        }

        if (deltaState.label !== undefined) {
            this.inputBox.label = deltaState.label;
        }

        if (deltaState.accessibility_label !== undefined) {
            this.inputBox.accessibilityLabel = deltaState.accessibility_label;
        }

        if (deltaState.style !== undefined) {
            this.inputBox.style = deltaState.style;
        }

        if (deltaState.prefix_text !== undefined) {
            this.inputBox.prefixText = deltaState.prefix_text;
        }

        if (deltaState.suffix_text !== undefined) {
            this.inputBox.suffixText = deltaState.suffix_text;
        }

        if (deltaState.is_secret !== undefined) {
            this.inputBox.inputElement.type = deltaState.is_secret
                ? "password"
                : "text";
        }

        if (deltaState.is_sensitive !== undefined) {
            this.inputBox.isSensitive = deltaState.is_sensitive;
        }

        if (deltaState.is_valid !== undefined) {
            this.inputBox.isValid = deltaState.is_valid;
        }
    }

    protected override getElementForKeyboardFocus(): HTMLElement {
        return this.inputBox.inputElement;
    }
}
