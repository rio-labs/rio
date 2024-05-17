import { ComponentBase, ComponentState } from './componentBase';
import { micromark } from 'micromark';

// This import decides which languages are supported by `highlight.js`. See
// their docs for details:
//
// https://github.com/highlightjs/highlight.js#importing-the-library
import hljs from 'highlight.js/lib/common';
import { Language } from 'highlight.js';

import { LayoutContext } from '../layouting';
import { getElementHeight, getElementWidth } from '../layoutHelpers';
import { firstDefined, isLocalUrl } from '../utils';
import { callRemoteMethodDiscardResponse } from '../rpc';
import { convertDivToCodeBlock } from './codeBlock';

export type MarkdownState = ComponentState & {
    _type_: 'Markdown-builtin';
    text?: string;
    default_language?: null | string;
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
    const codeBlocks = div.querySelectorAll('pre');
    codeBlocks.forEach((preElement) => {
        // Create a new div to hold the code block
        let codeBlockElement = document.createElement('div');
        preElement.parentNode!.insertBefore(codeBlockElement, preElement);

        // Get the text content of the code block
        let sourceCode = preElement.textContent ?? '';

        // Was a language specified?
        let codeElement = preElement.firstElementChild as HTMLElement;
        let specifiedLanguage: string = defaultLanguage ?? '';

        for (const cls of codeElement.classList) {
            if (cls.startsWith('language-')) {
                specifiedLanguage = cls.replace('language-', '');
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
        const inlineCodeBlocks = div.querySelectorAll('code');
        inlineCodeBlocks.forEach((codeElement) => {
            let hlResult = hljs.highlight(codeElement.textContent || '', {
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
    for (let link of div.getElementsByTagName('a')) {
        if (!isLocalUrl(link.href)) {
            continue;
        }

        link.addEventListener('click', (event) => {
            event.stopPropagation();
            event.preventDefault();

            callRemoteMethodDiscardResponse('openUrl', {
                url: link.href,
            });
        });
    }
}

export class MarkdownComponent extends ComponentBase {
    state: Required<MarkdownState>;

    // Since laying out markdown is time intensive, this component does its best
    // not to re-layout unless needed. This is done by setting the height
    // request lazily, and only if the width has changed. This value here is the
    // component's allocated width when the height request was last set.
    private heightRequestAssumesWidth: number;

    createElement(): HTMLElement {
        const element = document.createElement('div');
        element.classList.add('rio-markdown');
        return element;
    }

    updateElement(
        deltaState: MarkdownState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.text !== undefined) {
            // Create a new div to hold the markdown content. This is so the
            // layouting code can move it around as needed.
            let defaultLanguage = firstDefined(
                deltaState.default_language,
                this.state.default_language
            );

            convertMarkdown(deltaState.text, this.element, defaultLanguage);

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
