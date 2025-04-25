import { ComponentStatesUpdateContext } from "../componentManagement";
import { Debouncer } from "../debouncer";
import { markEventAsHandled, stopPropagation } from "../eventHandling";
import { InputBox, InputBoxStyle } from "../inputBox";
import { ComponentBase, DeltaState } from "./componentBase";
import {
    KeyboardFocusableComponent,
    KeyboardFocusableComponentState,
} from "./keyboardFocusableComponent";

export type MultiLineTextInputState = KeyboardFocusableComponentState & {
    _type_: "MultiLineTextInput-builtin";
    text: string;
    label: string;
    accessibility_label: string;
    style: InputBoxStyle;
    is_sensitive: boolean;
    is_valid: boolean;
    auto_adjust_height: boolean;
    reportFocusGain: boolean;
};

export class MultiLineTextInputComponent extends KeyboardFocusableComponent<MultiLineTextInputState> {
    private inputBox: InputBox;
    private onChangeLimiter: Debouncer;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let textarea = document.createElement("textarea");
        this.inputBox = new InputBox({ inputElement: textarea });

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
                    text: this.inputBox.value,
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

        // Detect `shift+enter` and send it to the backend
        //
        // In addition to notifying the backend, also include the input's
        // current value. This ensures any event handlers actually use the up-to
        // date value.
        this.inputBox.inputElement.addEventListener(
            "keydown",
            (event) => {
                if (event.key === "Enter" && event.shiftKey) {
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

        textarea.addEventListener("input", () => {
            if (this.state.auto_adjust_height) {
                this.fitHeightToText();
            }
        });

        return element;
    }

    updateElement(
        deltaState: DeltaState<MultiLineTextInputState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.text !== undefined) {
            this.inputBox.value = deltaState.text;

            let autoAdjustHeight =
                deltaState.auto_adjust_height ?? this.state.auto_adjust_height;
            if (autoAdjustHeight) {
                this.fitHeightToText();
            }
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

        if (deltaState.is_sensitive !== undefined) {
            this.inputBox.isSensitive = deltaState.is_sensitive;
        }

        if (deltaState.is_valid !== undefined) {
            this.inputBox.isValid = deltaState.is_valid;
        }

        if (deltaState.auto_adjust_height !== undefined) {
            if (deltaState.auto_adjust_height) {
                // We need a delay because the size is determined via
                // `textarea.scrollHeight`, which returns 0 if the textarea
                // isn't attached to the DOM yet. I tried
                // `requestAnimationFrame`, but the size was slightly off for
                // some reason.
                setTimeout(() => {
                    this.fitHeightToText();
                }, 50);
            } else {
                this.inputBox.inputElement.style.removeProperty("height");
            }
        }
    }

    fitHeightToText(): void {
        let textarea = this.inputBox.inputElement;
        textarea.style.minHeight = `${textarea.scrollHeight}px`;
    }

    protected override getElementForKeyboardFocus(): HTMLElement {
        return this.inputBox.inputElement;
    }
}
