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
        return document.createElement('div');
    }

    updateElement(
        deltaState: PlaceholderState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(latentComponents, deltaState._child_);
    }
}
