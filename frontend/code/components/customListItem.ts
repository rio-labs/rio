import { RippleEffect } from '../rippleEffect';
import { ComponentBase, ComponentState } from './componentBase';
import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';

const PADDING_X: number = 1.5;
const PADDING_Y: number = 0.7;

export type CustomListItemState = ComponentState & {
    _type_: 'CustomListItem-builtin';
    content?: ComponentId;
    pressable?: boolean;
};

export class CustomListItemComponent extends ComponentBase {
    state: Required<CustomListItemState>;

    // If this item has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;

    createElement(): HTMLElement {
        return document.createElement('div');
    }

    updateElement(
        deltaState: CustomListItemState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the child
        this.replaceOnlyChild(latentComponents, deltaState.content);

        // Style the surface depending on whether it is pressable
        if (deltaState.pressable === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(this.element);

                this.element.classList.add('rio-list-item-ripple');
                this.element.style.cursor = 'pointer';

                this.element.onclick = this._on_press.bind(this);
            }
        } else if (deltaState.pressable === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;

                this.element.classList.remove('rio-list-item-ripple');
                this.element.style.removeProperty('cursor');

                this.element.onclick = null;
            }
        }
    }

    private _on_press(): void {
        this.sendMessageToBackend({
            type: 'press',
        });
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth =
            componentsById[this.state.content]!.requestedWidth + PADDING_X * 2;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        componentsById[this.state.content]!.allocatedWidth =
            this.allocatedWidth - PADDING_X * 2;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight =
            componentsById[this.state.content]!.requestedHeight + PADDING_Y * 2;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        let child = componentsById[this.state.content]!;
        child.allocatedHeight = this.allocatedHeight - PADDING_Y * 2;

        // Position the child
        let element = child.element;
        element.style.left = `${PADDING_X}rem`;
        element.style.top = `${PADDING_Y}rem`;
    }
}
