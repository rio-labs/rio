import {
    componentsById,
    tryGetComponentByElement,
} from '../componentManagement';
import { ComponentId } from '../dataModels';
import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';

export type ScrollTargetState = ComponentState & {
    _type_: 'ScrollTarget-builtin';
    id?: string;
    content?: ComponentId | null;
    copy_button_content?: ComponentId | null;
    copy_button_text?: string | null;
};

export class ScrollTargetComponent extends ComponentBase {
    state: Required<ScrollTargetState>;

    linkElement: HTMLAnchorElement;
    buttonContainerElement: HTMLElement;
    cachedButtonTextSize: [number, number];

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-scroll-target');

        this.linkElement = document.createElement('a');
        element.appendChild(this.linkElement);

        this.buttonContainerElement = document.createElement('div');
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
            this.linkElement
        );

        if (deltaState.id !== undefined) {
            this.element.id = deltaState.id;
        }

        if (deltaState.copy_button_content !== undefined) {
            this._removeButtonChild(latentComponents);
            this.replaceOnlyChild(
                latentComponents,
                deltaState.copy_button_content,
                this.buttonContainerElement
            );
        } else if (deltaState.copy_button_text !== undefined) {
            this._removeButtonChild(latentComponents);

            let textElement = document.createElement('span');
            textElement.textContent = deltaState.copy_button_text;
            this.buttonContainerElement.appendChild(textElement);
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
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // The button component gets as much space as it requested, and the
        // other child gets all the rest
        let remainingWidth = this.allocatedWidth;

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
