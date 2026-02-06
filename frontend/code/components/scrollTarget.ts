import {
    ComponentStatesUpdateContext,
    tryGetComponentByElement,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import { setClipboard } from "../utils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type ScrollTargetState = ComponentState & {
    _type_: "ScrollTarget-builtin";
    id: string;
    content: ComponentId | null;
    copy_button_content: ComponentId | null;
    copy_button_text: string | null;
    copy_button_spacing: number;
};

export class ScrollTargetComponent extends ComponentBase<ScrollTargetState> {
    childContainerElement: HTMLElement;
    buttonContainerElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("a");
        element.classList.add("rio-scroll-target");

        this.childContainerElement = document.createElement("div");
        this.childContainerElement.classList.add(
            "rio-scroll-target-child-container"
        );
        element.appendChild(this.childContainerElement);

        this.buttonContainerElement = document.createElement("div");
        this.buttonContainerElement.classList.add(
            "rio-scroll-target-url-copy-button"
        );
        this.buttonContainerElement.addEventListener(
            "click",
            this._onUrlCopyButtonClick.bind(this)
        );
        element.appendChild(this.buttonContainerElement);

        return element;
    }

    updateElement(
        deltaState: DeltaState<ScrollTargetState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(
            context,
            deltaState.content,
            this.childContainerElement
        );

        if (deltaState.id !== undefined) {
            this.element.id = deltaState.id;
        }

        if (
            deltaState.copy_button_content !== undefined &&
            deltaState.copy_button_content !== null
        ) {
            this._removeButtonChild(context);
            this.replaceOnlyChild(
                context,
                deltaState.copy_button_content,
                this.buttonContainerElement
            );
        } else if (
            deltaState.copy_button_text !== undefined &&
            deltaState.copy_button_text !== null
        ) {
            this._removeButtonChild(context);

            // Use an <a> element so that
            // 1. Users can see the URL
            // 2. Users can right-click -> copy (They can copy the url just by
            //    clicking, but that's not obvious.)
            let linkElement = document.createElement("a");
            linkElement.href = `#${this.element.id}`;
            linkElement.style.textDecoration = "none"; // remove the underline
            linkElement.textContent = deltaState.copy_button_text;
            this.buttonContainerElement.appendChild(linkElement);
        }
    }

    private _removeButtonChild(context: ComponentStatesUpdateContext): void {
        let buttonChild = this.buttonContainerElement.firstElementChild;

        if (buttonChild === null) return;

        let childComponent = tryGetComponentByElement(buttonChild);
        if (childComponent === null) {
            buttonChild.remove();
        } else {
            this.replaceOnlyChild(
                context,
                childComponent.id,
                this.buttonContainerElement
            );
        }
    }

    private _onUrlCopyButtonClick(): void {
        let url = new URL(window.location.href);
        url.hash = this.state.id;

        setClipboard(url.toString());
    }
}
