import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";
import { hijackLinkElement } from "../utils";
import { applyIcon } from "../designApplication";

export type LinkState = ComponentState & {
    _type_: "Link-builtin";
    child_text?: string | null;
    child_component?: ComponentId | null;
    icon?: string | null;
    open_in_new_tab?: boolean;
    targetUrl: string;
};

export class LinkComponent extends ComponentBase {
    declare state: Required<LinkState>;

    createElement(): HTMLElement {
        let element = document.createElement("a");
        element.classList.add("rio-link");

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
        console.assert(
            this.element.childElementCount === 0,
            `${this} still has a child element after removeHtmlChild()`
        );
    }

    updateElement(
        deltaState: LinkState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        let element = this.element as HTMLAnchorElement;

        // Child Text?
        if (
            (deltaState.child_text !== undefined &&
                deltaState.child_text !== null) ||
            (this.state.child_text !== null && deltaState.icon !== undefined)
        ) {
            // Clear any existing children
            this.removeHtmlChild(latentComponents);

            // Add the icon, if any
            let icon = deltaState.icon ?? this.state.icon;

            if (icon !== null) {
                let iconElement = document.createElement("div");
                iconElement.classList.add("rio-text-link-icon");
                element.appendChild(iconElement);

                applyIcon(iconElement, icon, "currentColor");
            }

            // Add the new text
            let child_text = deltaState.child_text ?? this.state.child_text;

            let textElement = document.createElement("div");
            textElement.classList.add("rio-text-link-text");
            element.appendChild(textElement);
            textElement.textContent = child_text;

            // Update the CSS classes
            element.classList.add("rio-text-link");
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
            element.classList.remove("rio-text-link");
        }

        // Target URL?
        if (deltaState.targetUrl !== undefined) {
            element.href = deltaState.targetUrl;
        }

        // Open in new tab?
        if (deltaState.open_in_new_tab === true) {
            element.target = "_blank";
        } else if (deltaState.open_in_new_tab === false) {
            element.target = "";
        }
    }
}
