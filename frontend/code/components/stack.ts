import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { SingleContainer } from './singleContainer';

export type StackState = ComponentState & {
    _type_: 'Stack-builtin';
    children?: ComponentId[];
};

export class StackComponent extends SingleContainer {
    state: Required<StackState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-stack');
        return element;
    }

    updateElement(
        deltaState: StackState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceChildren(latentComponents, deltaState.children);
    }
}
