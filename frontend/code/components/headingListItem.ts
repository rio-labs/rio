import { ComponentBase, ComponentState } from './componentBase';
import { textStyleToCss } from '../cssUtils';
import { getTextDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';

const PADDING_LEFT: number = 1.0;
const PADDING_TOP: number = 1.3;
const PADDING_RIGHT: number = 1.0;
const PADDING_BOTTOM: number = 0.3;

export type HeadingListItemState = ComponentState & {
    _type_: 'HeadingListItem-builtin';
    text?: string;
};

export class HeadingListItemComponent extends ComponentBase {
    state: Required<HeadingListItemState>;

    private textWidth: number;
    private textHeight: number;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-heading-list-item');

        // Apply a style. This could be done with CSS, instead of doing it
        // individually for each component, but these are rare and this preempts
        // duplicate code.
        Object.assign(element.style, textStyleToCss('heading3'));

        // Apply the padding
        element.style.paddingLeft = `${PADDING_LEFT}rem`;
        element.style.paddingTop = `${PADDING_TOP}rem`;
        element.style.paddingRight = `${PADDING_RIGHT}rem`;
        element.style.paddingBottom = `${PADDING_BOTTOM}rem`;

        return element;
    }

    updateElement(
        deltaState: HeadingListItemState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.text !== undefined) {
            this.element.textContent = deltaState.text;

            // Cache the text's dimensions
            [this.textWidth, this.textHeight] = getTextDimensions(
                deltaState.text,
                'heading3'
            );

            this.makeLayoutDirty();
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = PADDING_LEFT + this.textWidth + PADDING_RIGHT;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {}

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = PADDING_TOP + this.textHeight + PADDING_BOTTOM;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {}
}
