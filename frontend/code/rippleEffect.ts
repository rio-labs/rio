import { commitCss } from "./utils";

class RippleEffectOptions {
    rippleDuration?: number;
    rippleCssColor?: string;
    triggerOnPress?: boolean;
    customCss?: { [attr: string]: string };
}

export class RippleEffect {
    public customCss: { [attr: string]: string };

    private element: HTMLElement;

    private rippleDuration: number;
    private rippleCssColor: string;

    private boundEventHandler: (event: MouseEvent) => void;

    constructor(
        element: HTMLElement,
        {
            rippleDuration = 0.9,
            rippleCssColor = "var(--rio-local-text-color)",
            triggerOnPress = true,
            customCss = {},
        }: RippleEffectOptions = {}
    ) {
        this.element = element;
        this.rippleDuration = rippleDuration;
        this.rippleCssColor = rippleCssColor;
        this.customCss = customCss;

        // Subscribe to events
        if (triggerOnPress) {
            this.boundEventHandler = this.trigger.bind(this);
            this.element.addEventListener("click", this.boundEventHandler);
        }
    }

    destroy() {
        if (this.boundEventHandler !== undefined) {
            this.element.removeEventListener("click", this.boundEventHandler);
        }
    }

    trigger(event: MouseEvent) {
        // Find the ripple's origin
        const rect = this.element.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Spawn two elements: one for the animation, and one with `overflow:
        // hidden`
        let rippleContainer = document.createElement("div");
        rippleContainer.classList.add(
            "rio-ripple-container",
            "rio-not-a-child-component"
        );
        rippleContainer.style.setProperty(
            "--rio-ripple-color",
            this.rippleCssColor
        );
        rippleContainer.style.setProperty(
            "--rio-ripple-duration",
            `${this.rippleDuration}s`
        );
        Object.assign(rippleContainer.style, this.customCss);
        this.element.appendChild(rippleContainer);

        let rippleElement = document.createElement("div");
        rippleElement.classList.add("rio-ripple-effect");
        rippleContainer.appendChild(rippleElement);

        // Position it
        rippleElement.style.top = `${y}px`;
        rippleElement.style.left = `${x}px`;

        rippleElement.style.width = "0px";
        rippleElement.style.height = "0px";

        rippleElement.style.opacity = "0.1";

        // Commit CSS
        commitCss(rippleElement);

        // Animate it
        rippleElement.style.top = `${rect.height / 2}px`;
        rippleElement.style.left = `${rect.width / 2}px`;

        let size = Math.max(rect.width, rect.height) * 2;
        rippleElement.style.width = `${size}px`;
        rippleElement.style.height = `${size}px`;

        rippleElement.style.opacity = "0";

        // Remove the ripple element after the animation
        setTimeout(() => {
            rippleContainer.remove();
        }, this.rippleDuration * 1000);
    }
}
