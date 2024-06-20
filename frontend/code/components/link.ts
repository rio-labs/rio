import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { hijackLinkElement } from '../utils';

export type LinkState = ComponentState & {
    _type_: 'Link-builtin';
    child_text?: string | null;
    child_component?: ComponentId | null;
    open_in_new_tab?: boolean;
    targetUrl: string;
};

export class LinkComponent extends ComponentBase {
    state: Required<LinkState>;

    createElement(): HTMLElement {
        let element = document.createElement('a');
        element.classList.add('rio-link');

        hijackLinkElement(element);

        return element;
    }

    removeHtmlChild(latentComponents: Set<ComponentBase>) {
        /// If `element` has a child, remove it. There mustn't be more than one.

        // Components need special consideration, since they're tracked
        if (this.state.child_component !== null) {
            this.replaceOnlyChild(latentComponents, null);
            return;
        }

        // Plain HTML elements can be removed directly
        if (this.state.child_text !== null) {
            let element = this.element as HTMLAnchorElement;
            while (element.firstChild) {
                element.removeChild(element.firstChild);
            }
        }

        // There should be no children left
        console.assert(this.element.childElementCount === 0);
    }

    updateElement(
        deltaState: LinkState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        let element = this.element as HTMLAnchorElement;

        // Child Text?
        if (
            deltaState.child_text !== undefined &&
            deltaState.child_text !== null
        ) {
            // Clear any existing children
            this.removeHtmlChild(latentComponents);

            // Add the new text
            let textElement = document.createElement('div');
            element.appendChild(textElement);
            textElement.textContent = deltaState.child_text;

            // Update the CSS classes
            element.classList.add('rio-text-link');
        }

        // Child Component?
        if (
            deltaState.child_component !== undefined &&
            deltaState.child_component !== null
        ) {
            // Clear any existing children
            this.removeHtmlChild(latentComponents);

            // Add the new component
            this.replaceOnlyChild(latentComponents, deltaState.child_component);

            // Update the CSS classes
            element.classList.remove('rio-text-link');
        }

        // Target URL?
        if (deltaState.targetUrl !== undefined) {
            element.href = deltaState.targetUrl;
        }

        // Open in new tab?
        if (deltaState.open_in_new_tab === true) {
            element.target = '_blank';
        } else if (deltaState.open_in_new_tab === false) {
            element.target = '';
        }
    }
}
