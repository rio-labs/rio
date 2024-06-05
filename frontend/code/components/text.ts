import { TextStyle } from '../dataModels';
import { textStyleToCss } from '../cssUtils';
import { ComponentBase, ComponentState } from './componentBase';
import { LayoutContext } from '../layouting';
import { getTextDimensions } from '../layoutHelpers';

export type TextState = ComponentState & {
    _type_: 'Text-builtin';
    text?: string;
    selectable?: boolean;
    style?: 'heading1' | 'heading2' | 'heading3' | 'text' | 'dim' | TextStyle;
    justify?: 'left' | 'right' | 'center' | 'justify';
    wrap?: boolean | 'ellipsize';
};

export class TextComponent extends ComponentBase {
    state: Required<TextState>;

    private inner: HTMLElement;
    private cachedNoWrapDimensions: [number, number];

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-text');

        this.inner = document.createElement('span');
        element.appendChild(this.inner);

        return element;
    }

    updateElement(
        deltaState: TextState,
        latentComponents: Set<ComponentBase>
    ): void {
        // BEFORE WE DO ANYTHING ELSE, update the text style
        if (deltaState.style !== undefined) {
            // Change the element to <h1>, <h2>, <h3> or <span> as necessary
            let tagName: string = 'SPAN';
            if (typeof deltaState.style === 'string') {
                tagName =
                    {
                        heading1: 'H1',
                        heading2: 'H2',
                        heading3: 'H3',
                    }[deltaState.style] || 'SPAN';
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

        // Wrap lines
        switch (deltaState.wrap) {
            case false:
                this.inner.style.whiteSpace = 'pre';
                this.inner.style.textOverflow = 'clip';
                break;
            case true:
                this.inner.style.whiteSpace = 'pre-wrap';
                this.inner.style.textOverflow = 'clip';
                break;
            case 'ellipsize':
                this.inner.style.whiteSpace = 'pre';
                this.inner.style.textOverflow = 'ellipsis';
                break;
        }

        // Selectable
        if (deltaState.selectable !== undefined) {
            this.inner.style.pointerEvents = deltaState.selectable
                ? 'auto'
                : 'none';
        }

        // Text alignment
        if (deltaState.justify !== undefined) {
            this.inner.style.textAlign = deltaState.justify;
        }

        if (
            deltaState.text !== undefined ||
            deltaState.wrap !== undefined ||
            deltaState.style !== undefined
        ) {
            this.makeLayoutDirty();

            // Compute and cache the dimensions that our text requires if line
            // wrapping is disabled
            this.cachedNoWrapDimensions = getTextDimensions(
                this.element.textContent!,
                this.state.style
            );
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        if (this.state.wrap === false) {
            this.naturalWidth = this.cachedNoWrapDimensions[0];
        } else {
            this.naturalWidth = 0;
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        if (this.state.wrap === true) {
            // Calculate how much height we need given the allocated width
            this.naturalHeight = getTextDimensions(
                this.state.text,
                this.state.style,
                this.allocatedWidth
            )[1];
        } else {
            // 'wrap' and 'ellipsize' both require the same height
            this.naturalHeight = this.cachedNoWrapDimensions[1];
        }
    }
}
