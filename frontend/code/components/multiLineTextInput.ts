import { markEventAsHandled } from "../eventHandling";
import { InputBox, InputBoxStyle } from "../inputBox";
import { ComponentBase, ComponentState } from "./componentBase";

export type MultiLineTextInputState = ComponentState & {
    _type_: "MultiLineTextInput-builtin";
    text?: string;
    label?: string;
    accessibility_label?: string;
    style?: InputBoxStyle;
    is_sensitive?: boolean;
    is_valid?: boolean;
};

export class MultiLineTextInputComponent extends ComponentBase {
    declare state: Required<MultiLineTextInputState>;

    private inputBox: InputBox;

    createElement(): HTMLElement {
        let textarea = document.createElement("textarea");
        this.inputBox = new InputBox({ inputElement: textarea });

        let element = this.inputBox.outerElement;
        element.classList.add("rio-multi-line-text-input");

        this.inputBox.inputElement.addEventListener("blur", () => {
            this.setStateAndNotifyBackend({
                text: this.inputBox.value,
            });
        });

        // Detect `shift+enter` and send it to the backend
        //
        // In addition to notifying the backend, also include the input's
        // current value. This ensures any event handlers actually use the up-to
        // date value.
        this.inputBox.inputElement.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && event.shiftKey) {
                this.state.text = this.inputBox.value;
                this.sendMessageToBackend({
                    text: this.state.text,
                });

                markEventAsHandled(event);
            }
        });

        // Eat click events so the element can't be clicked-through
        element.addEventListener("click", (event) => {
            event.stopPropagation();
            event.stopImmediatePropagation();
        });

        element.addEventListener("pointerdown", (event) => {
            event.stopPropagation();
            event.stopImmediatePropagation();
        });

        element.addEventListener("pointerup", (event) => {
            event.stopPropagation();
            event.stopImmediatePropagation();
        });

        return element;
    }

    updateElement(
        deltaState: MultiLineTextInputState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

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

        if (deltaState.is_sensitive !== undefined) {
            this.inputBox.isSensitive = deltaState.is_sensitive;
        }

        if (deltaState.is_valid !== undefined) {
            this.inputBox.isValid = deltaState.is_valid;
        }
    }

    grabKeyboardFocus(): void {
        this.inputBox.focus();
    }
}
