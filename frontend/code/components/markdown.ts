import { ComponentBase, ComponentState } from "./componentBase";
import { micromark } from "micromark";

// This import decides which languages are supported by `highlight.js`. See
// their docs for details:
//
// https://github.com/highlightjs/highlight.js#importing-the-library
import hljs from "highlight.js/lib/common";

import { firstDefined, hijackLinkElement } from "../utils";
import { convertDivToCodeBlock } from "./codeBlock";

export type MarkdownState = ComponentState & {
    _type_: "Markdown-builtin";
    text?: string;
    default_language?: null | string;
    selectable?: boolean;
    justify?: "left" | "right" | "center" | "justify";
    overflow?: "nowrap" | "wrap" | "ellipsize";
};

// Convert a Markdown string to HTML and render it in the given div.
function convertMarkdown(
    markdownSource: string,
    div: HTMLElement,
    defaultLanguage: null | string
) {
    // Drop the default language if it isn't supported or recognized
    if (
        defaultLanguage !== null &&
        hljs.getLanguage(defaultLanguage) === undefined
    ) {
        defaultLanguage = null;
    }

    // Convert the Markdown content to HTML
    div.innerHTML = micromark(markdownSource);

    // Post-process some of the generated HTML elements
    enhanceCodeBlocks(div, defaultLanguage);
    highlightInlineCode(div, defaultLanguage);
    hijackLocalLinks(div);
}

function enhanceCodeBlocks(
    div: HTMLElement,
    defaultLanguage: string | null
): void {
    const codeBlocks = div.querySelectorAll("pre");
    codeBlocks.forEach((preElement) => {
        // Create a new div to hold the code block
        let codeBlockElement = document.createElement("div");
        preElement.parentNode!.insertBefore(codeBlockElement, preElement);

        // Get the text content of the code block
        let sourceCode = preElement.textContent ?? "";

        // Was a language specified?
        let codeElement = preElement.firstElementChild as HTMLElement;
        let specifiedLanguage: string = defaultLanguage ?? "";

        for (const cls of codeElement.classList) {
            if (cls.startsWith("language-")) {
                specifiedLanguage = cls.replace("language-", "");
                break;
            }
        }

        // Rio ships with a dedicated code block component. Delegate the work to
        // that.
        convertDivToCodeBlock(
            codeBlockElement,
            sourceCode,
            specifiedLanguage,
            true
        );

        // Delete the original code block
        preElement.remove();
    });
}

function highlightInlineCode(
    div: HTMLElement,
    defaultLanguage: string | null
): void {
    // Since these are very short, guessing the language probably isn't a great
    // idea. Only do this if a default language was specified.
    //
    // TODO: What if most code blocks had the same language specified? Use the
    // same one here?
    if (defaultLanguage !== null) {
        const inlineCodeBlocks = div.querySelectorAll("code");
        inlineCodeBlocks.forEach((codeElement) => {
            let hlResult = hljs.highlight(codeElement.textContent || "", {
                language: defaultLanguage!,
                ignoreIllegals: true,
            });

            codeElement.innerHTML = hlResult.value;
        });
    }
}

function hijackLocalLinks(div: HTMLElement): void {
    // Clicking a link makes the browser navigate to the URL, which is
    // unnecessary if the URL points to the rio app - there's no need to close
    // the current session and create a new one. So we'll hijack all of those
    // links.
    for (let link of div.getElementsByTagName("a")) {
        hijackLinkElement(link);
    }
}

export class MarkdownComponent extends ComponentBase {
    declare state: Required<MarkdownState>;

    createElement(): HTMLElement {
        const element = document.createElement("div");
        element.classList.add("rio-markdown");
        return element;
    }

    updateElement(
        deltaState: MarkdownState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.text !== undefined) {
            // Create a new div to hold the markdown content. This is so the
            // layouting code can move it around as needed.
            let defaultLanguage = firstDefined(
                deltaState.default_language,
                this.state.default_language
            );

            convertMarkdown(deltaState.text, this.element, defaultLanguage);
        }

        // Handle overlong text
        if (deltaState.overflow !== undefined) {
            this.element.dataset.overflow = deltaState.overflow;
        }

        // Selectable
        if (deltaState.selectable !== undefined) {
            if (deltaState.selectable) {
                this.element.style.pointerEvents = "auto";
                this.element.style.userSelect = "auto";
            } else {
                this.element.style.pointerEvents = "none";
                this.element.style.userSelect = "none";
            }
        }

        // Text alignment
        if (deltaState.justify !== undefined) {
            this.element.style.textAlign = deltaState.justify;
        }
    }
}
