import { ComponentBase, ComponentState } from "./componentBase";

export type HtmlState = ComponentState & {
    _type_: "Html-builtin";
    html?: string;
};

export class HtmlComponent extends ComponentBase {
    declare state: Required<HtmlState>;

    private isInitialized = false;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-html");
        return element;
    }

    runScriptsInElement(): void {
        for (let oldScriptElement of this.element.querySelectorAll("script")) {
            // Create a new script element
            const newScriptElement = document.createElement("script");

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
        super.updateElement(deltaState, latentComponents);

        if (deltaState.html !== undefined) {
            // If the HTML hasn't actually changed from last time, don't do
            // anything. This is important so scripts don't get re-executed each
            // time the component is updated.
            if (deltaState.html === this.state.html && this.isInitialized) {
                return;
            }

            // Load the HTML
            this.element.innerHTML = deltaState.html;

            // Just setting the innerHTML doesn't run scripts. Do that manually.
            this.runScriptsInElement();
        }

        this.isInitialized = true;
    }
}
