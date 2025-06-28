import {
    Color,
    SolidFill,
    LinearGradientFill,
    ImageFill,
    TextStyle,
} from "../dataModels";
import { applyTextStyleCss, textfillToCss, textStyleToCss } from "../cssUtils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type TextState = ComponentState & {
    _type_: "Text-builtin";
    text: string;
    selectable: boolean;
    style: "heading1" | "heading2" | "heading3" | "text" | "dim" | TextStyle;
    justify: "left" | "right" | "center" | "justify";
    overflow: "nowrap" | "wrap" | "ellipsize";

    font: string | null;
    fill: Color | SolidFill | LinearGradientFill | ImageFill | null;
    font_size: number | null;
    italic: boolean | null;
    font_weight: "normal" | "bold" | null;
    underlined: boolean | null;
    strikethrough: boolean | null;
    all_caps: boolean | null;
};

export class TextComponent extends ComponentBase<TextState> {
    private inner: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-text");

        this.inner = document.createElement("span");
        element.appendChild(this.inner);

        return element;
    }

    updateElement(
        deltaState: DeltaState<TextState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // BEFORE WE DO ANYTHING ELSE, replace the inner HTML element
        if (deltaState.style !== undefined) {
            // Change the element to <h1>, <h2>, <h3> or <span> as necessary
            let tagName: string = "SPAN";
            if (typeof deltaState.style === "string") {
                tagName =
                    {
                        heading1: "H1",
                        heading2: "H2",
                        heading3: "H3",
                    }[deltaState.style] || "SPAN";
            }

            if (tagName !== this.inner.tagName) {
                let newInner = document.createElement(tagName);

                this.inner.remove();
                this.element.appendChild(newInner);
                this.inner = newInner;

                // Turn the whole state into a deltaState so that the new
                // element is initialized correctly
                deltaState = { ...this.state, ...deltaState };

                // Shut up the type checker
                if (deltaState.style === undefined) {
                    return;
                }
            }
        }

        // Styling
        if (
            deltaState.style !== undefined ||
            deltaState.font !== undefined ||
            deltaState.fill !== undefined ||
            deltaState.font_size !== undefined ||
            deltaState.italic !== undefined ||
            deltaState.font_weight !== undefined ||
            deltaState.underlined !== undefined ||
            deltaState.strikethrough !== undefined ||
            deltaState.all_caps !== undefined
        ) {
            // Update the state so the following code doesn't have to check both
            // state and deltaState
            Object.assign(this.state, deltaState);

            // Get the CSS for the text style
            let textStyleCss = textStyleToCss(this.state.style);

            // Apply any overrides
            if (this.state.font !== null) {
                textStyleCss["font-family"] = this.state.font;
            }

            if (this.state.fill !== null) {
                Object.assign(textStyleCss, textfillToCss(this.state.fill));
            }

            if (this.state.font_size !== null) {
                textStyleCss["font-size"] = `${this.state.font_size}rem`;
            }

            if (this.state.italic !== null) {
                textStyleCss["font-style"] = this.state.italic
                    ? "italic"
                    : "normal";
            }

            if (this.state.font_weight != null) {
                textStyleCss["font-weight"] = this.state.font_weight;
            }

            let textDecorations: string[] = [];

            if (this.state.underlined === true) {
                textDecorations.push("underline");
            }

            if (this.state.strikethrough === true) {
                textDecorations.push("line-through");
            }

            textStyleCss["text-decoration"] = textDecorations.join(" ");

            if (this.state.all_caps !== null) {
                textStyleCss["text-transform"] = this.state.all_caps
                    ? "uppercase"
                    : "none";
            }

            applyTextStyleCss(this.inner, textStyleCss);
        }

        // Text content
        if (deltaState.text !== undefined) {
            this.inner.textContent = deltaState.text;
        }

        // How to handle overlong text?
        switch (deltaState.overflow) {
            case "nowrap":
                this.inner.style.whiteSpace = "pre";
                this.inner.style.width = "max-content";
                this.inner.style.textOverflow = "clip";
                this.inner.style.overflow = "unset";
                break;
            case "wrap":
                this.inner.style.whiteSpace = "pre-wrap";
                this.inner.style.width = "min-content";
                this.inner.style.textOverflow = "clip";
                this.inner.style.overflow = "unset";
                break;
            case "ellipsize":
                this.inner.style.whiteSpace = "pre";
                this.inner.style.width = "0"; // No `min-width: 100%` required
                this.inner.style.textOverflow = "ellipsis";

                // The element must have `overflow: hidden`. In theory it should
                // be fine for this setting to be permanent, but in practice it
                // sometimes cuts off a pixel of text. So unfortunately have to
                // turn it on via JS here.
                this.inner.style.overflow = "hidden";
                break;
        }

        // Selectable
        if (deltaState.selectable !== undefined) {
            if (deltaState.selectable) {
                this.inner.style.pointerEvents = "auto";
                this.inner.style.userSelect = "auto";
            } else {
                this.inner.style.pointerEvents = "none";
                this.inner.style.userSelect = "none";
            }
        }

        // Text alignment
        if (deltaState.justify !== undefined) {
            this.inner.style.textAlign = deltaState.justify;
        }
    }
}
