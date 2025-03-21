import { applySwitcheroo } from "../designApplication";
import { ColorSet, ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { RippleEffect } from "../rippleEffect";
import { markEventAsHandled } from "../eventHandling";
import { getAllocatedHeightInPx, getAllocatedWidthInPx } from "../utils";

type AbstractButtonState = ComponentState & {
    shape: "pill" | "rounded" | "rectangle" | "circle";
    style: "major" | "minor" | "colored-text" | "plain-text";
    color: ColorSet;
    content: ComponentId;
    is_sensitive: boolean;
};

abstract class AbstractButtonComponent extends ComponentBase<AbstractButtonState> {
    // This is the element with the `rio-button` class. The subclass is
    // responsible for creating it (by calling `createButtonElement()`).
    protected buttonElement: HTMLElement;

    private childContainer: HTMLElement;

    private rippleInstance: RippleEffect;

    // In order to prevent a newly created button from being clicked on
    // accident, it starts out disabled and enables itself after a short delay.
    private isStillInitiallyDisabled: boolean = true;

    protected createButtonElement(): HTMLElement {
        // Create the element
        let element = document.createElement("div");
        element.classList.add("rio-button");

        this.childContainer = document.createElement("div");
        element.appendChild(this.childContainer);

        // Add a material ripple effect
        this.rippleInstance = new RippleEffect(element, {
            triggerOnPress: false,
        });

        // Detect button presses
        element.onclick = (event) => {
            markEventAsHandled(event);

            // Do nothing if the button isn't sensitive
            if (!this.state["is_sensitive"] || this.isStillInitiallyDisabled) {
                return;
            }

            this.rippleInstance.trigger(event);

            // Otherwise notify the backend
            this.sendMessageToBackend({
                type: "press",
            });
        };

        setTimeout(() => {
            this.isStillInitiallyDisabled = false;
        }, 350);

        return element;
    }

    updateElement(
        deltaState: DeltaState<AbstractButtonState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the child
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.childContainer
        );

        // Set the shape
        if (deltaState.shape !== undefined) {
            this.buttonElement.classList.remove(
                "rio-shape-pill",
                "rio-shape-rounded",
                "rio-shape-rectangle",
                "rio-shape-circle"
            );

            let className = "rio-shape-" + deltaState.shape;
            this.buttonElement.classList.add(className);
        }

        // Set the style
        if (deltaState.style !== undefined) {
            this.childContainer.classList.remove(
                "rio-buttonstyle-major",
                "rio-buttonstyle-minor",
                "rio-buttonstyle-colored-text",
                "rio-buttonstyle-plain-text"
            );

            let className = "rio-buttonstyle-" + deltaState.style;
            this.childContainer.classList.add(className);
        }

        // Apply the color
        //
        // If no new colorset is specified, bump to the next palette. This
        // allows all styles to just assume that the palette they should use is
        // the current one.
        if (deltaState.color !== undefined || deltaState.style !== undefined) {
            let colorSet = deltaState.color ?? this.state.color;

            applySwitcheroo(
                this.childContainer,
                colorSet === "keep" ? "bump" : colorSet
            );
        }

        // Sensitive?
        if (deltaState.is_sensitive !== undefined) {
            this.childContainer.classList.toggle(
                "rio-insensitive",
                !deltaState.is_sensitive
            );
        }
    }
}

export type ButtonState = AbstractButtonState & {
    _type_: "Button-builtin";
};

export class ButtonComponent extends AbstractButtonComponent {
    createElement(): HTMLElement {
        this.buttonElement = this.createButtonElement();
        this.buttonElement.role = "button";
        return this.buttonElement;
    }
}

export type IconButtonState = AbstractButtonState & {
    _type_: "IconButton-builtin";
    icon: string;
};

export class IconButtonComponent extends AbstractButtonComponent {
    private resizeObserver: ResizeObserver;

    protected createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-icon-button");
        element.role = "button";

        this.buttonElement = this.createButtonElement();
        element.appendChild(this.buttonElement);

        // Watch the element for size changes, to preserve the aspect ratio
        // of the icon.
        this.resizeObserver = new ResizeObserver(this.onResize.bind(this));
        this.resizeObserver.observe(element);

        return element;
    }

    onDestruction(): void {
        super.onDestruction();

        this.resizeObserver.disconnect();
    }

    private onResize(): void {
        let targetSize = Math.min(
            getAllocatedWidthInPx(this.buttonElement),
            getAllocatedHeightInPx(this.buttonElement)
        );

        this.buttonElement.style.width = `${targetSize}px`;
        this.buttonElement.style.height = `${targetSize}px`;
    }
}
