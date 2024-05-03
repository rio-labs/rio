import { applyColorSet } from '../designApplication';
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

    private innerElement: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-theme-context-switcher');

        this.innerElement = document.createElement('div');
        element.appendChild(this.innerElement);

        return element;
    }

    updateElement(
        deltaState: ThemeContextSwitcherState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the child
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.innerElement
        );

        // Colorize
        if (deltaState.color !== undefined) {
            applyColorSet(this.element, this.innerElement, deltaState.color);
        }
    }
}
