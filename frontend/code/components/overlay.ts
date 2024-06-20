import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type OverlayState = ComponentState & {
    _type_: 'Overlay-builtin';
    content?: ComponentId;
};

export class OverlayComponent extends ComponentBase {
    state: Required<OverlayState>;

    private overlayElement: HTMLElement;

    createElement(): HTMLElement {
        this.overlayElement = document.createElement('div');
        this.overlayElement.classList.add('rio-overlay');
        document.body.firstChild!.appendChild(this.overlayElement);

        return document.createElement('div');
    }

    updateElement(
        deltaState: OverlayState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.overlayElement
        );
    }
}
