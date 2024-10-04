import { ComponentBase, ComponentState } from "./componentBase";

// This import decides which languages are supported by `highlight.js`. See
// their docs for details:
//
// https://github.com/highlightjs/highlight.js#importing-the-library
import hljs from "highlight.js/lib/common";
import { Language } from "highlight.js";

import { setClipboard } from "../utils";
import { applyIcon } from "../designApplication";
import { markEventAsHandled } from "../eventHandling";

export type CodeBlockState = ComponentState & {
    _type_: "CodeBlock-builtin";
    code?: string;
    language?: string | null;
    show_controls?: boolean;
};

/// Contains additional aliases for languages that are not recognized by
/// highlight.js
const languageAliases: { [key: string]: string } = {
    none: "plaintext",
    null: "plaintext",
    plain: "plaintext",
};

// Converts a `<div>` element into a code block. This is handled externally so
// it can also be used by the markdown component.
export function convertDivToCodeBlock(
    div: HTMLDivElement,
    code: string,
    language: string | null,
    displayControls: boolean
) {
    // Spawn the necessary HTML
    div.classList.add("rio-code-block");
    div.innerHTML = `
        <div class="rio-code-block-header">
            <div class="rio-code-block-language"></div>
            <button class="rio-code-block-copy-button">Copy code</button>
        </div>
        <pre></pre>
    `;

    let headerElement = div.querySelector(
        ".rio-code-block-header"
    ) as HTMLDivElement;

    let labelElement = headerElement.querySelector(
        ".rio-code-block-language"
    ) as HTMLDivElement;

    let copyButton = headerElement.querySelector(
        ".rio-code-block-copy-button"
    ) as HTMLButtonElement;

    let preElement = div.querySelector("pre") as HTMLPreElement;

    // Support additional language aliases
    if (language !== null && languageAliases[language] !== undefined) {
        language = languageAliases[language];
    }

    // See if hljs recognizes the language
    if (language !== null && hljs.getLanguage(language) === undefined) {
        language = null;
    }

    // Strip any empty leading/trailing lines from the code.
    //
    // From the front, only newlines are removed so that the indentation stays
    // intact.
    //
    // From the end, any and all whitespace is removed.
    code = code ? code.replace(/^\n+|\s+$/g, "") : "";

    // Add syntax highlighting and apply the source code. This will also detect
    // the actual language.
    let hljsLanguage: Language | undefined = undefined;

    if (language === null) {
        let hlResult = hljs.highlightAuto(code);
        preElement.innerHTML = hlResult.value;

        if (hlResult.language !== undefined) {
            hljsLanguage = hljs.getLanguage(hlResult.language);
        }
    } else {
        let hlResult = hljs.highlight(code, {
            language: language,
            ignoreIllegals: true,
        });
        preElement.innerHTML = hlResult.value;

        hljsLanguage = hljs.getLanguage(language);
    }

    // Are controls enabled?
    if (displayControls) {
        // What's the language's name?
        let languageNiceName = hljsLanguage?.name ?? "";
        labelElement.textContent = languageNiceName;

        // Initialize the copy button
        applyIcon(copyButton, "material/content_copy");

        copyButton.addEventListener("click", (event) => {
            const codeToCopy = (preElement as HTMLPreElement).textContent ?? "";

            setClipboard(codeToCopy);

            copyButton.title = "Copied!";
            applyIcon(copyButton, "material/done");

            setTimeout(() => {
                copyButton.title = "Copy code";
                applyIcon(copyButton, "material/content_copy");
            }, 5000);

            markEventAsHandled(event);
        });
    } else {
        headerElement.remove();
    }
}

export class CodeBlockComponent extends ComponentBase {
    declare state: Required<CodeBlockState>;

    createElement(): HTMLElement {
        const element = document.createElement("div");
        return element;
    }

    updateElement(
        deltaState: CodeBlockState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Re-create the code block
        convertDivToCodeBlock(
            this.element as HTMLDivElement,
            deltaState.code ?? this.state.code,
            deltaState.language ?? this.state.language,
            deltaState.show_controls ?? this.state.show_controls
        );
    }
}
