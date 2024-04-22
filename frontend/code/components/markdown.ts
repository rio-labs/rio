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
import { copyToClipboard, firstDefined } from '../utils';
import { applyIcon } from '../designApplication';

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

    // Enhance code blocks
    const codeBlocks = div.querySelectorAll('pre code');
    codeBlocks.forEach((codeBlockInner) => {
        codeBlockInner = codeBlockInner as HTMLElement;

        // Remove empty leading/trailing lines
        codeBlockInner.textContent = codeBlockInner.textContent
            ? codeBlockInner.textContent.replace(/^\n+|\n+$/g, '')
            : '';

        // Was a language specified?
        let specifiedLanguage: string | null = defaultLanguage;
        for (const cls of codeBlockInner.classList) {
            if (cls.startsWith('language-')) {
                specifiedLanguage = cls.replace('language-', '');
                break;
            }
        }

        // See if this language is supported
        if (
            specifiedLanguage !== null &&
            hljs.getLanguage(specifiedLanguage) === undefined
        ) {
            specifiedLanguage = null;
        }

        // Add syntax highlighting. This will also detect the actual
        // language.
        let language: Language | undefined = undefined;

        if (specifiedLanguage === null) {
            let hlResult = hljs.highlightAuto(codeBlockInner.textContent);
            codeBlockInner.innerHTML = hlResult.value;

            if (hlResult.language !== undefined) {
                language = hljs.getLanguage(hlResult.language);
            }
        } else {
            let hlResult = hljs.highlight(codeBlockInner.textContent, {
                language: specifiedLanguage,
                ignoreIllegals: true,
            });
            codeBlockInner.innerHTML = hlResult.value;
            language = hljs.getLanguage(specifiedLanguage);
        }

        let languageNiceName = language?.name ?? '';

        // Get the language from the code block class (if specified)
        // const languageClass = codeBlockInner.className.split(' ').find((cls) =>
        //     cls.startsWith('language-')
        // );
        // const language = languageClass ? languageClass.replace('language-', '') : '';

        // Wrap the code block. This outer element will hold additional components
        // and styling.
        let codeBlockOuter = document.createElement('div');
        codeBlockOuter.classList.add('rio-markdown-code-block');

        codeBlockOuter.innerHTML = `<div class="rio-markdown-code-block-header"><div class="rio-markdown-code-block-language">${languageNiceName}</div><button class="rio-markdown-code-block-copy-button">Copy code</button></div>`;

        codeBlockInner.parentNode!.insertBefore(codeBlockOuter, codeBlockInner);
        codeBlockOuter.appendChild(codeBlockInner);

        // Create a copy button
        let copyButton = codeBlockOuter.querySelector(
            '.rio-markdown-code-block-copy-button'
        ) as HTMLButtonElement;

        copyButton.title = 'Copy code';
        applyIcon(
            copyButton,
            'material/content-copy',
            'var(--rio-local-text-color)'
        );

        copyButton.addEventListener('click', (event) => {
            const codeToCopy =
                (codeBlockInner as HTMLElement).textContent ?? '';

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
    });

    // Highlight inline code
    //
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

export class MarkdownComponent extends ComponentBase {
    state: Required<MarkdownState>;

    // Since laying out markdown is time intensive, this component does its best
    // not to re-layout unless needed. This is done by setting the height
    // request lazily, and only if the width has changed. This value here is the
    // component's allocated width when the height request was last set.
    private heightRequestAssumesWidth: number;

    createElement(): HTMLElement {
        const element = document.createElement('div');
        element.classList.add('rio-markdown-view');
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
