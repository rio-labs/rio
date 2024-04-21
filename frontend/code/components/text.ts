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

        this.inner = document.createElement('div');
        element.appendChild(this.inner);

        return element;
    }

    updateElement(
        deltaState: TextState,
        latentComponents: Set<ComponentBase>
    ): void {
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

        // Text style
        if (deltaState.style !== undefined) {
            Object.assign(this.inner.style, textStyleToCss(deltaState.style));
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
