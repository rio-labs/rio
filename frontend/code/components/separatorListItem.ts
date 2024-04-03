import { ComponentBase, ComponentState } from './componentBase';
import { LayoutContext } from '../layouting';

export type SeparatorListItemState = ComponentState & {
    _type_: 'SeparatorListItem-builtin';
};

export class SeparatorListItemComponent extends ComponentBase {
    state: Required<SeparatorListItemState>;

    createElement(): HTMLElement {
        return document.createElement('div');
    }

    updateElement(
        deltaState: SeparatorListItemState,
        latentComponents: Set<ComponentBase>
    ): void {}

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 0;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {}

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 1;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {}
}
