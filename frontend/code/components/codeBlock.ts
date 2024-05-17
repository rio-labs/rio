import { ComponentBase, ComponentState } from './componentBase';

// This import decides which languages are supported by `highlight.js`. See
// their docs for details:
//
// https://github.com/highlightjs/highlight.js#importing-the-library
import hljs from 'highlight.js/lib/common';
import { Language } from 'highlight.js';

import { LayoutContext } from '../layouting';
import { getElementHeight, getElementWidth } from '../layoutHelpers';
import { copyToClipboard, firstDefined } from '../utils';
import { applyIcon } from '../designApplication';

export type CodeBlockState = ComponentState & {
    _type_: 'CodeBlock-builtin';
    code?: string;
    language?: string | null;
    display_controls?: boolean;
};

/// Contains additional aliases for languages that are not recognized by
/// highlight.js
const languageAliases: { [key: string]: string } = {
    none: 'plaintext',
    null: 'plaintext',
    plain: 'plaintext',
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
    div.classList.add('rio-code-block');
    div.innerHTML = `
        <div class="rio-code-block-header">
            <div class="rio-code-block-language"></div>
            <button class="rio-code-block-copy-button">Copy code</button>
        </div>
        <pre></pre>
    `;

    let headerElement = div.querySelector(
        '.rio-code-block-header'
    ) as HTMLDivElement;

    let labelElement = headerElement.querySelector(
        '.rio-code-block-language'
    ) as HTMLDivElement;

    let copyButton = headerElement.querySelector(
        '.rio-code-block-copy-button'
    ) as HTMLButtonElement;

    let preElement = div.querySelector('pre') as HTMLPreElement;

    // Support additional language aliases
    if (language !== null && languageAliases[language] !== undefined) {
        language = languageAliases[language];
    }

    // See if hljs recognizes the language
    if (language !== null && hljs.getLanguage(language) === undefined) {
        language = null;
    }

    // Strip any empty leading/trailing lines from the code
    code = code ? code.replace(/^\n+|\n+$/g, '') : '';

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
        let languageNiceName = hljsLanguage?.name ?? '';
        labelElement.textContent = languageNiceName;

        // Initialize the copy button
        applyIcon(
            copyButton,
            'material/content-copy',
            'var(--rio-local-text-color)'
        );

        copyButton.addEventListener('click', (event) => {
            const codeToCopy = (preElement as HTMLPreElement).textContent ?? '';

            copyToClipboard(codeToCopy);

            copyButton.title = 'Copied!';
            applyIcon(
                copyButton,
                'material/done',
                'var(--rio-local-text-color)'
            );

            setTimeout(() => {
                copyButton.title = 'Copy code';
                applyIcon(
                    copyButton,
                    'material/content-copy',
                    'var(--rio-local-text-color)'
                );
            }, 5000);

            event.stopPropagation();
        });
    } else {
        headerElement.remove();
    }
}

export class CodeBlockComponent extends ComponentBase {
    state: Required<CodeBlockState>;

    // Since laying out an entire codeblock may be intensive, this component
    // does its best not to re-layout unless needed. This is done by setting the
    // height request lazily, and only if the width has changed. This value here
    // is the component's allocated width when the height request was last set.
    private heightRequestAssumesWidth: number;

    createElement(): HTMLElement {
        const element = document.createElement('div');
        return element;
    }

    updateElement(
        deltaState: CodeBlockState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Find the value sto use
        let code = firstDefined(deltaState.code, this.state.code);

        let language = firstDefined(deltaState.language, this.state.language);

        let displayControls = firstDefined(
            deltaState.display_controls,
            this.state.display_controls
        );

        // Re-create the code block
        convertDivToCodeBlock(
            this.element as HTMLDivElement,
            code,
            language,
            displayControls
        );

        // Update the width request
        //
        // For some reason the element takes up the whole parent's width
        // without explicitly setting its width
        this.element.style.width = 'min-content';
        this.naturalWidth = getElementWidth(this.element);

        // Any previously calculated height request is no longer valid
        this.heightRequestAssumesWidth = -1;
        this.makeLayoutDirty();
    }

    updateNaturalWidth(ctx: LayoutContext): void {}

    updateAllocatedWidth(ctx: LayoutContext): void {}

    updateNaturalHeight(ctx: LayoutContext): void {
        // Is the previous height request still value?
        if (this.heightRequestAssumesWidth === this.allocatedWidth) {
            return;
        }

        // No, re-layout
        this.element.style.height = 'min-content';
        this.naturalHeight = getElementHeight(this.element);
        this.heightRequestAssumesWidth = this.allocatedWidth;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {}
}
