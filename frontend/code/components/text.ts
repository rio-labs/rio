import { TextStyle } from "../dataModels";
import { textStyleToCss } from "../cssUtils";
import { ComponentBase, ComponentState } from "./componentBase";

export type TextState = ComponentState & {
    _type_: "Text-builtin";
    text?: string;
    selectable?: boolean;
    style?: "heading1" | "heading2" | "heading3" | "text" | "dim" | TextStyle;
    justify?: "left" | "right" | "center" | "justify";
    overflow?: "nowrap" | "wrap" | "ellipsize";
};

export class TextComponent extends ComponentBase {
    declare state: Required<TextState>;

    private inner: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-text");

        this.inner = document.createElement("span");
        element.appendChild(this.inner);

        return element;
    }

    updateElement(
        deltaState: TextState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // BEFORE WE DO ANYTHING ELSE, update the text style
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

            // Now apply the style
            Object.assign(this.inner.style, textStyleToCss(deltaState.style));
        }

        // Text content
        //
        // Make sure not to allow any linebreaks if the text is not multiline.
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
