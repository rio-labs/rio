import { ComponentId } from '../models';
import { ComponentBase, ComponentState } from './componentBase';
import { SingleContainer } from './singleContainer';

export type ScrollTargetState = ComponentState & {
    _type_: 'ScrollTarget-builtin';
    id?: string;
    content?: ComponentId | null;
};

export class ScrollTargetComponent extends SingleContainer {
    state: Required<ScrollTargetState>;

    createElement(): HTMLElement {
        return document.createElement('a');
    }

    updateElement(
        deltaState: ScrollTargetState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(latentComponents, deltaState.content);

        if (deltaState.id !== undefined) {
            this.element.id = deltaState.id;
        }
    }
}
