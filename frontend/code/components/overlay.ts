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

    private onWindowResize: () => void;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-overlay');

        // When the window is resized, we need re-layouting. This isn't
        // guaranteed to happen automatically, because if a parent component's
        // size doesn't change, then its children won't be re-layouted. So we
        // have to explicitly listen for the resize event and mark ourselves as
        // dirty.
        //
        // The `capture: true` is there to ensure that we're already marked as
        // dirty when the re-layout is triggered.
        this.onWindowResize = this.makeLayoutDirty.bind(this);
        window.addEventListener('resize', this.onWindowResize, {
            capture: true,
        });

        return element;
    }

    onDestruction(): void {
        window.removeEventListener('resize', this.onWindowResize);
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
