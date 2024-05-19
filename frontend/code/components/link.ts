import { componentsById } from '../componentManagement';
import { getTextDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { navigateToUrl } from '../utils';

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

        // Listen for clicks
        element.addEventListener(
            'click',
            (event: MouseEvent) => {
                // If the link opens in a new tab, we can let the browser handle
                // it
                if (this.state.open_in_new_tab) {
                    return;
                }

                // Otherwise, we don't want to needlessly reload the page. We'll
                // keep our websocket connection open and tell the backend to
                // change the active URL
                event.stopPropagation();
                event.preventDefault();
                navigateToUrl(this.state.targetUrl);
            },
            true
        );

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

    updateNaturalWidth(ctx: LayoutContext): void {
        if (this.state.child_component === null) {
            [this.naturalWidth, this.naturalHeight] = getTextDimensions(
                this.state.child_text!,
                'text'
            );
        } else {
            this.naturalWidth =
                componentsById[this.state.child_component]!.requestedWidth;
        }
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        if (this.state.child_component !== null) {
            componentsById[this.state.child_component]!.allocatedWidth =
                this.allocatedWidth;
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        if (this.state.child_component === null) {
            // Already set in updateRequestedWidth
        } else {
            this.naturalHeight =
                componentsById[this.state.child_component]!.requestedHeight;
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        if (this.state.child_component !== null) {
            componentsById[this.state.child_component]!.allocatedHeight =
                this.allocatedHeight;

            let element = componentsById[this.state.child_component]!.element;
            element.style.left = '0';
            element.style.top = '0';
        }
    }
}
