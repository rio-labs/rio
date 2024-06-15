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
        return element;
    }

    onDestruction(): void {
        window.removeEventListener('resize', this.onWindowResize);
    }

    updateElement(
        deltaState: OverlayState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(latentComponents, deltaState.content);
    }
}
