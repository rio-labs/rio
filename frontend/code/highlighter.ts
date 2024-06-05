/// Helper class for highlighting components.

export class Highlighter {
    private highlighter: HTMLElement;

    constructor() {
        // Create the highlighter and hide it
        this.highlighter = document.createElement('div');
        this.highlighter.classList.add('rio-dev-tools-component-highlighter');
        document.body.appendChild(this.highlighter);

        this.moveTo(null);
    }

    destroy() {
        this.highlighter.remove();
    }

    /// Transition the highlighter to the given component. If the component is
    /// `null`, transition it out.
    public moveTo(target: HTMLElement | null) {
        // If no component is to be highlighted, make the highlighter the size
        // of the window, effectively hiding it. Overshoot by a bit to make sure
        // the highlighter's pulse animation doesn't make it visible by
        // accident.
        let left, top, width, height;

        if (target === null) {
            left = -10;
            top = -10;
            width = window.innerWidth + 20;
            height = window.innerHeight + 20;
        } else {
            let rect = target.getBoundingClientRect();
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
