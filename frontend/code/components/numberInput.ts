import { DeltaState } from "./componentBase";
import { InputBox, InputBoxStyle } from "../inputBox";
import { markEventAsHandled, stopPropagation } from "../eventHandling";
import {
    KeyboardFocusableComponent,
    KeyboardFocusableComponentState,
} from "./keyboardFocusableComponent";

import Mexp from "math-expression-evaluator";
import { ComponentStatesUpdateContext } from "../componentManagement";

const mathExpressionEvaluator = new Mexp();

const MULTIPLIER_SUFFIXES = {
    k: 1_000,
    m: 1_000_000,
};
const SUFFIX_REGEX = new RegExp(
    `([+-]?\\d+(?:\\.\\d+)?)([${Object.keys(MULTIPLIER_SUFFIXES).join("")}])`,
    "gi"
);

export type NumberInputState = KeyboardFocusableComponentState & {
    _type_: "NumberInput-builtin";
    value: number;
    label: string;
    accessibility_label: string;
    style: InputBoxStyle;
    prefix_text: string;
    suffix_text: string;
    minimum: number | null;
    maximum: number | null;
    decimals: number;
    decimal_separator: string;
    thousands_separator: string;
    is_sensitive: boolean;
    is_valid: boolean;
    reportFocusGain: boolean;
};

export class NumberInputComponent extends KeyboardFocusableComponent<NumberInputState> {
    private inputBox: InputBox;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Note: We don't use `<input type="number">` because:
        // 1. Phones will display the number keyboard, preventing users from
        //    inputting suffixes or math equations
        // 2. Its up/down buttons are ugly
        this.inputBox = new InputBox();

        let element = this.inputBox.outerElement;

        // Detect focus gain...
        this.inputBox.inputElement.addEventListener("focus", () => {
            if (this.state.reportFocusGain) {
                this.sendMessageToBackend({
                    type: "gainFocus",
                    value: this.state.value,
                });
            }
        });

        // ...and focus loss
        this.inputBox.inputElement.addEventListener("blur", () => {
            this._commitInput();

            this.sendMessageToBackend({
                type: "loseFocus",
                value: this.state.value,
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
                    // Commit the input
                    this._commitInput();

                    // Inform the backend
                    this.sendMessageToBackend({
                        type: "confirm",
                        value: this.state.value,
                    });

                    markEventAsHandled(event);
                } else if (event.key === "ArrowUp") {
                    this._onArrowKeyPress(1);
                    markEventAsHandled(event);
                } else if (event.key === "ArrowDown") {
                    this._onArrowKeyPress(-1);
                    markEventAsHandled(event);
                }
            },
            { capture: true }
        );

        // Eat click events so the element can't be clicked-through
        element.addEventListener("click", stopPropagation);
        element.addEventListener("pointerdown", stopPropagation);
        element.addEventListener("pointerup", stopPropagation);

        return element;
    }

    updateElement(
        deltaState: DeltaState<NumberInputState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

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

        if (deltaState.is_sensitive !== undefined) {
            this.inputBox.isSensitive = deltaState.is_sensitive;
        }

        if (deltaState.is_valid !== undefined) {
            this.inputBox.isValid = deltaState.is_valid;
        }

        if (deltaState.decimals !== undefined) {
            this.inputBox.inputElement.inputMode =
                deltaState.decimals === 0 ? "numeric" : "decimal";
        }

        if (
            deltaState.value !== undefined ||
            deltaState.decimals !== undefined
        ) {
            Object.assign(this.state, deltaState);
            this._updateDisplayedValue();
        }
    }

    /// This function should be called whenever the user is done entering input.
    /// It will try to parse the input, update the input's text content, and
    /// update the state.
    private _commitInput(): void {
        let value: number;
        try {
            value = this._parseValue(this.inputBox.value);
        } catch (error) {
            console.log(
                `Failed to parse NumberInput value "${this.inputBox.value}": ${error}`
            );
            return;
        }

        this._clampAndSetValue(value);
    }

    private _clampAndSetValue(value: number): void {
        // Clamp it
        if (this.state.minimum !== null) {
            value = Math.max(this.state.minimum, value);
        }

        if (this.state.maximum !== null) {
            value = Math.min(this.state.maximum, value);
        }

        // Set it
        this.state.value = value;
        this._updateDisplayedValue();
    }

    private _onArrowKeyPress(multiplier: number): void {
        this._commitInput();

        let newValue = this.state.value + multiplier * this._getStepSize();
        this._clampAndSetValue(newValue);
    }

    /// How much to increment/decrement the value when the up- or down-arrows
    /// are pressed
    private _getStepSize(): number {
        return Math.pow(10, -this.state.decimals);
    }

    private _parseValue(rawValue: string): number {
        // If left empty, set the value to 0 or whatever the minimum is
        if (rawValue.trim().length === 0) {
            if (this.state.minimum !== null) {
                return this.state.minimum;
            }

            if (this.state.maximum !== null && this.state.maximum < 0) {
                return this.state.maximum;
            }

            return 0;
        }

        // Remove thousand separators
        rawValue = rawValue.replaceAll(this.state.thousands_separator, "");

        // Normalize decimal separators
        rawValue = rawValue.replaceAll(this.state.decimal_separator, ".");

        // Convert suffixes to multiplications
        rawValue = rawValue.replace(SUFFIX_REGEX, (match) => {
            let suffix = match.charAt(
                match.length - 1
            ) as keyof typeof MULTIPLIER_SUFFIXES;

            return `(${match.substring(0, match.length - 1)} * ${
                MULTIPLIER_SUFFIXES[suffix]
            })`;
        });

        // Evaluate the expression
        let value = mathExpressionEvaluator.eval(rawValue);

        // Round it
        value = round(value, this.state.decimals);

        return value;
    }

    private _updateDisplayedValue(): void {
        let intStr: string;
        let fracStr: string;

        if (this.state.decimals === 0) {
            intStr = this.state.value.toFixed(0);
            fracStr = "";
        } else {
            let numStr = this.state.value.toFixed(this.state.decimals);
            [intStr, fracStr] = numStr.split(".");
        }

        // Add the thousands separators
        intStr = parseInt(intStr)
            .toLocaleString("en")
            .replaceAll(",", this.state.thousands_separator);

        // Construct the final formatted number
        let result: string;
        if (this.state.decimals === 0) {
            result = intStr;
        } else {
            result = `${intStr}${this.state.decimal_separator}${fracStr}`;
        }

        this.inputBox.value = result;
    }

    protected override getElementForKeyboardFocus(): HTMLElement {
        return this.inputBox.inputElement;
    }
}

function round(value: number, decimals: number): number {
    let multiplier = Math.pow(10, decimals);
    return Math.round((value + Number.EPSILON) * multiplier) / multiplier;
}
