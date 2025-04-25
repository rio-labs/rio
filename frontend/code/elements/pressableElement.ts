import { markEventAsHandled } from "../eventHandling";

/// An unstyled element that behaves like a button, with all the necessary
/// accessibility features.
///
/// If `onPress` is null, the element stops being a button.
export class PressableElement extends HTMLElement {
    public onPress: ((event: PointerEvent | KeyboardEvent) => void) | null =
        null;

    constructor() {
        super();

        let shadowRoot = this.attachShadow({ mode: "closed" });

        shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            cursor: pointer;
          }

          :host(:focus) {
            outline: 2px solid var(--focus-color, Highlight);
            outline-offset: 2px;
          }
        </style>
        <slot></slot>
      `;

        this.onClick = this.onClick.bind(this);
        this.onKeyPress = this.onKeyPress.bind(this);
    }

    connectedCallback() {
        this.setAttribute("role", "button");
        this.setAttribute("tabindex", "0"); // Make it focusable
        this.addEventListener("click", this.onClick);
        this.addEventListener("keydown", this.onKeyPress);
    }

    disconnectedCallback() {
        this.removeEventListener("click", this.onClick);
        this.removeEventListener("keydown", this.onKeyPress);
    }

    private onClick(event: PointerEvent) {
        this.emitPressEvent(event);
        markEventAsHandled(event);
    }

    private onKeyPress(event: KeyboardEvent) {
        if (event.key === "Enter" || event.key === " ") {
            this.emitPressEvent(event);
            markEventAsHandled(event);
        }
    }

    private emitPressEvent(event: PointerEvent | KeyboardEvent) {
        if (this.onPress !== null) {
            this.onPress(event);
        }
    }
}

customElements.define("rio-pressable-element", PressableElement);
