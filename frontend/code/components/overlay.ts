import { componentsById, getRootComponent } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type OverlayState = ComponentState & {
    _type_: 'Overlay-builtin';
    content?: ComponentId;
};

export class OverlayComponent extends ComponentBase {
    state: Required<OverlayState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-overlay');
        return element;
    }

    updateElement(
        deltaState: OverlayState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(latentComponents, deltaState.content);
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // The root component keeps track of the correct overlay size. Take it
        // from there. To heck with what the parent says.
        let root = getRootComponent();
        componentsById[this.state.content]!.allocatedWidth = root.overlayWidth;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Honor the global overlay height.
        let root = getRootComponent();
        componentsById[this.state.content]!.allocatedHeight =
            root.overlayHeight;

        // Position the child
        let element = componentsById[this.state.content]!.element;
        element.style.left = '0';
        element.style.top = '0';
    }
}
