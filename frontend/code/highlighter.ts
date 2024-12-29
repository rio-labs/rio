/// Helper class for highlighting components.

import { getRootComponent } from "./componentManagement";

export class Highlighter {
    private target: Element | null = null;
    private intervalHandlerId: number | undefined = undefined;
    private highlighter: HTMLElement;

    constructor() {
        // Create the highlighter and hide it
        this.highlighter = document.createElement("div");
        this.highlighter.classList.add("rio-dev-tools-component-highlighter");

        getRootComponent().devToolsHighlighterContainer.appendChild(
            this.highlighter
        );

        this.moveTo(null);
    }

    destroy(): void {
        this.highlighter.remove();
        clearInterval(this.intervalHandlerId);
    }

    /// Transition the highlighter to the given component. If the component is
    /// `null`, transition it out.
    public moveTo(target: HTMLElement | null): void {
        this.target = target;
        this.updatePosition();

        // If the element is moved or resized or if the user scrolls, the
        // position of the highlighter becomes wrong. So we'll register a
        // handler that periodically updates it.
        clearInterval(this.intervalHandlerId);

        if (target !== null) {
            this.intervalHandlerId = setInterval(
                () => this.updatePosition(),
                100
            );
        }
    }

    private updatePosition(): void {
        // If no component is to be highlighted, make the highlighter the size
        // of the window, effectively hiding it. Overshoot by a bit to make sure
        // the highlighter's pulse animation doesn't make it visible by
        // accident.
        let left: number, top: number, width: number, height: number;

        if (this.target === null) {
            left = -10;
            top = -10;
            width = window.innerWidth + 20;
            height = window.innerHeight + 20;
        } else {
            let rect = this.target.getBoundingClientRect();
            left = rect.left;
            top = rect.top;
            width = rect.width;
            height = rect.height;
        }

        // Move the highlighter
        this.highlighter.style.top = `${top}px`;
        this.highlighter.style.left = `${left}px`;
        this.highlighter.style.width = `${width}px`;
        this.highlighter.style.height = `${height}px`;
    }
}
