import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type AlignState = ComponentState & {
    _type_: 'Align-builtin';
    content?: ComponentId;
    align_x?: number | null;
    align_y?: number | null;
};

export class AlignComponent extends ComponentBase {
    state: Required<AlignState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        return element;
    }

    updateElement(
        deltaState: AlignState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(latentComponents, deltaState.content);

        if (
            deltaState.align_x !== undefined ||
            deltaState.align_y !== undefined
        ) {
            this.makeLayoutDirty();
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = componentsById[this.state.content]!.requestedWidth;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        let child = componentsById[this.state.content]!;

        if (this.state.align_x === null) {
            child.allocatedWidth = this.allocatedWidth;
            child.element.style.left = '0';
        } else {
            child.allocatedWidth = child.requestedWidth;

            let additionalSpace = this.allocatedWidth - child.requestedWidth;
            child.element.style.left =
                additionalSpace * this.state.align_x + 'rem';
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight =
            componentsById[this.state.content]!.requestedHeight;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        let child = componentsById[this.state.content]!;

        if (this.state.align_y === null) {
            child.allocatedHeight = this.allocatedHeight;
            child.element.style.top = '0';
        } else {
            child.allocatedHeight = child.requestedHeight;

            let additionalSpace = this.allocatedHeight - child.requestedHeight;
            child.element.style.top =
                additionalSpace * this.state.align_y + 'rem';
        }
    }
}
