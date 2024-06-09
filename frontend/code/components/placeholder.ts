import { SingleContainer } from './singleContainer';
import { ComponentBase, ComponentState } from './componentBase';
import { ComponentId } from '../dataModels';

export type PlaceholderState = ComponentState & {
    _type_: 'Placeholder'; // Not 'Placeholder-builtin'!
    _child_?: ComponentId;
};

export class PlaceholderComponent extends SingleContainer {
    state: Required<PlaceholderState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-placeholder');
        return element;
    }

    updateElement(
        deltaState: PlaceholderState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(latentComponents, deltaState._child_);
    }
}
