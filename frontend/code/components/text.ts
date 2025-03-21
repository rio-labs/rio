import {
    Color,
    SolidFill,
    LinearGradientFill,
    ImageFill,
    TextStyle,
} from "../dataModels";
import { textfillToCss, textStyleToCss } from "../cssUtils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type TextState = ComponentState & {
    _type_: "Text-builtin";
    text: string;
    selectable: boolean;
    style: "heading1" | "heading2" | "heading3" | "text" | "dim" | TextStyle;
    justify: "left" | "right" | "center" | "justify";
    overflow: "nowrap" | "wrap" | "ellipsize";

    font: string | null;
    fill:
        | Color
        | SolidFill
        | LinearGradientFill
        | ImageFill
        | null
        | "not given";
    font_size: number | null;
    italic: boolean | null;
    font_weight: "normal" | "bold" | null;
    underlined: boolean | null;
    strikethrough: boolean | null;
    all_caps: boolean | null;
};

export class TextComponent extends ComponentBase<TextState> {
    private inner: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-text");

        this.inner = document.createElement("span");
        element.appendChild(this.inner);

        return element;
    }

    updateElement(
        deltaState: DeltaState<TextState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

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
            let textStyleCss = textStyleToCss(
                deltaState.style ?? this.state.style
            );

            if (deltaState.font) {
                textStyleCss["font-family"] = deltaState.font;
            }

            if (
                deltaState.fill !== undefined &&
                deltaState.fill !== "not given"
            ) {
                Object.assign(textStyleCss, textfillToCss(deltaState.fill));
            }

            if (deltaState.font_size) {
                textStyleCss["font-size"] = `${deltaState.font_size}rem`;
            }

            if (deltaState.italic) {
                textStyleCss["font-style"] = deltaState.italic
                    ? "italic"
                    : "normal";
            }

            if (deltaState.font_weight) {
                textStyleCss["font-weight"] = deltaState.font_weight;
            }

            let textDecorations: string[] = [];

            if (deltaState.underlined) {
                textDecorations.push("underline");
            }

            if (deltaState.strikethrough) {
                textDecorations.push("line-through");
            }

            textStyleCss["text-decoration"] = textDecorations.join(" ");

            if (deltaState.all_caps) {
                textStyleCss["text-transform"] = deltaState.all_caps
                    ? "uppercase"
                    : "none";
            }

            Object.assign(this.inner.style, textStyleCss);
        }

        // Text content
        if (deltaState.text !== undefined) {
            this.inner.textContent = deltaState.text;
        }

        // How to handle overlong text?
        switch (deltaState.overflow) {
            case "nowrap":
                this.inner.style.whiteSpace = "pre";
                this.inner.style.textOverflow = "clip";
                this.inner.style.width = "max-content";
                break;
            case "wrap":
                this.inner.style.whiteSpace = "pre-wrap";
                this.inner.style.textOverflow = "clip";
                this.inner.style.width = "min-content";
                break;
            case "ellipsize":
                this.inner.style.whiteSpace = "pre";
                this.inner.style.textOverflow = "ellipsis";
                this.inner.style.width = "0"; // No `min-width: 100%` required
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
