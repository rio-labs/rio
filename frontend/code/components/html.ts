import { getElementDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
import { firstDefined } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';

export type HtmlState = ComponentState & {
    _type_: 'Html-builtin';
    html?: string;
};

export class HtmlComponent extends ComponentBase {
    state: Required<HtmlState>;

    private containerElement: HTMLElement;

    private previousHtml: string = '';

    createElement(): HTMLElement {
        let element = document.createElement('div');

        this.containerElement = document.createElement('div');
        element.appendChild(this.containerElement);

        return element;
    }

    runScriptsInElement(element: HTMLElement): void {
        for (let oldScriptElement of this.containerElement.querySelectorAll(
            'script'
        )) {
            console.debug('Running script', oldScriptElement.innerText);

            // Create a new script element
            const newScriptElement = document.createElement('script');

            // Copy over all attributes
            for (let i = 0; i < oldScriptElement.attributes.length; i++) {
                const attr = oldScriptElement.attributes[i];
                newScriptElement.setAttribute(attr.name, attr.value);
            }

            // And the source itself
            newScriptElement.appendChild(
                document.createTextNode(oldScriptElement.innerHTML)
            );

            // Finally replace the old script element with the new one so
            // the browser executes it
            oldScriptElement.parentNode!.replaceChild(
                newScriptElement,
                oldScriptElement
            );
        }
    }

    updateElement(
        deltaState: HtmlState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.html !== undefined) {
            // If the HTML hasn't actually changed from last time, don't do
            // anything. This is important so scripts don't get re-executed each
            // time the component is updated.
            if (deltaState.html === this.previousHtml) {
                return;
            }
            this.previousHtml = deltaState.html;

            // Load the HTML
            this.containerElement.innerHTML = deltaState.html;

            // Just setting the innerHTML doesn't run scripts. Do that manually.
            this.runScriptsInElement(this.containerElement);

            // Determine the dimensions of the HTML element
            [this.naturalWidth, this.naturalHeight] = getElementDimensions(
                this.containerElement
            );
            this.makeLayoutDirty();
        }
    }
}
