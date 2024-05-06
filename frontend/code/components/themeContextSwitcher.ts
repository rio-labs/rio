import { applySwitcheroo } from '../designApplication';
import { ColorSet, ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { SingleContainer } from './singleContainer';

export type ThemeContextSwitcherState = ComponentState & {
    _type_: 'ThemeContextSwitcher-builtin';
    content?: ComponentId;
    color?: ColorSet;
};

export class ThemeContextSwitcherComponent extends SingleContainer {
    state: Required<ThemeContextSwitcherState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        return element;
    }

    updateElement(
        deltaState: ThemeContextSwitcherState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the child
        this.replaceOnlyChild(latentComponents, deltaState.content);

        // Colorize
        if (deltaState.color !== undefined) {
            applySwitcheroo(this.element, deltaState.color);
        }
    }
}
