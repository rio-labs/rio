import { SingleContainer } from './singleContainer';
import { ComponentBase, ComponentState } from './componentBase';
import { ComponentId } from '../dataModels';

export type ClassContainerState = ComponentState & {
    _type_: 'ClassContainer-builtin';
    content?: ComponentId | null;
    classes?: string[];
};

export class ClassContainerComponent extends SingleContainer {
    state: Required<ClassContainerState>;

    createElement(): HTMLElement {
        return document.createElement('div');
    }

    updateElement(
        deltaState: ClassContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(latentComponents, deltaState.content);

        if (deltaState.classes !== undefined) {
            // Remove all old values
            this.element.className = '';

            // Add all new values
            this.element.classList.add(...deltaState.classes);
        }
    }
}
