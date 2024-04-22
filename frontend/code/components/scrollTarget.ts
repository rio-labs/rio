import {
    componentsById,
    tryGetComponentByElement,
} from '../componentManagement';
import { ComponentId } from '../dataModels';
import { getTextDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
import { copyToClipboard } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';

export type ScrollTargetState = ComponentState & {
    _type_: 'ScrollTarget-builtin';
    id?: string;
    content?: ComponentId | null;
    copy_button_content?: ComponentId | null;
    copy_button_text?: string | null;
    copy_button_spacing?: number;
};

export class ScrollTargetComponent extends ComponentBase {
    state: Required<ScrollTargetState>;

    childContainerElement: HTMLElement;
    buttonContainerElement: HTMLElement;
    cachedButtonTextSize: [number, number];

    createElement(): HTMLElement {
        let element = document.createElement('a');
        element.classList.add('rio-scroll-target');

        this.childContainerElement = document.createElement('div');
        element.appendChild(this.childContainerElement);

        this.buttonContainerElement = document.createElement('div');
        this.buttonContainerElement.classList.add(
            'rio-scroll-target-url-copy-button'
        );
        this.buttonContainerElement.addEventListener(
            'click',
            this._onUrlCopyButtonClick.bind(this)
        );
        element.appendChild(this.buttonContainerElement);

        return element;
    }

    updateElement(
        deltaState: ScrollTargetState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.childContainerElement
        );

        if (deltaState.id !== undefined) {
            this.element.id = deltaState.id;
        }

        if (
            deltaState.copy_button_content !== undefined &&
            deltaState.copy_button_content !== null
        ) {
            this._removeButtonChild(latentComponents);
            this.replaceOnlyChild(
                latentComponents,
                deltaState.copy_button_content,
                this.buttonContainerElement
            );
        } else if (
            deltaState.copy_button_text !== undefined &&
            deltaState.copy_button_text !== null
        ) {
            this._removeButtonChild(latentComponents);

            let textElement = document.createElement('span');
            textElement.textContent = deltaState.copy_button_text;
            this.buttonContainerElement.appendChild(textElement);

            this.cachedButtonTextSize = getTextDimensions(
                deltaState.copy_button_text,
                'text'
            );
        }
    }

    private _removeButtonChild(latentComponents: Set<ComponentBase>): void {
        let buttonChild = this.buttonContainerElement.firstElementChild;

        if (buttonChild === null) return;

        let childComponent = tryGetComponentByElement(buttonChild);
        if (childComponent === null) {
            buttonChild.remove();
        } else {
            this.replaceOnlyChild(
                latentComponents,
                childComponent.id,
                this.buttonContainerElement
            );
        }
    }

    private _onUrlCopyButtonClick(): void {
        let url = new URL(window.location.href);
        url.hash = this.state.id;

        copyToClipboard(url.toString());
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        if (this.state.content === null) {
            this.naturalWidth = 0;
        } else {
            this.naturalWidth =
                componentsById[this.state.content]!.requestedWidth;
        }

        if (this.state.copy_button_content !== null) {
            this.naturalWidth +=
                componentsById[this.state.copy_button_content]!.requestedWidth;
        } else if (this.state.copy_button_text !== null) {
            this.naturalWidth += this.cachedButtonTextSize[0];
        }

        // If both children exist, add the spacing
        if (
            this.state.content !== null &&
            (this.state.copy_button_content !== null ||
                this.state.copy_button_text !== null)
        ) {
            this.naturalWidth += this.state.copy_button_spacing;
        }
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // The button component gets as much space as it requested, and the
        // other child gets all the rest
        let remainingWidth =
            this.allocatedWidth - this.state.copy_button_spacing;
        let buttonX = 0;

        if (this.state.copy_button_content !== null) {
            let buttonComponent =
                componentsById[this.state.copy_button_content]!;

            buttonComponent.allocatedWidth = buttonComponent.requestedWidth;
            remainingWidth -= buttonComponent.allocatedWidth;
        } else if (this.state.copy_button_text !== null) {
            remainingWidth -= this.cachedButtonTextSize[0];
        }

        if (this.state.content !== null) {
            componentsById[this.state.content]!.allocatedWidth = remainingWidth;
            buttonX = remainingWidth + this.state.copy_button_spacing;
        }

        if (
            this.state.copy_button_content !== null ||
            this.state.copy_button_text !== null
        ) {
            let childElement = this.buttonContainerElement
                .firstElementChild as HTMLElement;
            childElement.style.left = `${buttonX}rem`;
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        let contentHeight = 0;
        let copyButtonHeight = 0;

        if (this.state.content !== null) {
            contentHeight = componentsById[this.state.content]!.requestedHeight;
        }

        if (this.state.copy_button_content !== null) {
            copyButtonHeight =
                componentsById[this.state.copy_button_content]!.requestedHeight;
        } else if (this.state.copy_button_text !== null) {
            copyButtonHeight = this.cachedButtonTextSize[1];
        }

        this.naturalHeight = Math.max(contentHeight, copyButtonHeight);
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        if (this.state.content !== null) {
            componentsById[this.state.content]!.allocatedHeight =
                this.allocatedHeight;
        }

        if (this.state.copy_button_content !== null) {
            componentsById[this.state.copy_button_content]!.allocatedHeight =
                this.allocatedHeight;
        }
    }
}
