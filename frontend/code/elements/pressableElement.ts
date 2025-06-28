import { markEventAsHandled } from "../eventHandling";

/// An unstyled element that behaves like a button, with all the necessary
/// accessibility features.
///
/// If `onPress` is null, the element stops being a button.
export class PressableElement extends HTMLElement {
    private _customRole: string | null;
    private _onPress: ((event: PointerEvent | KeyboardEvent) => void) | null =
        null;
    private _isSensitive: boolean = true;

    constructor({ role = null }: { role?: string | null } = {}) {
        super();

        this._customRole = role;
        this.role = role ?? "button";

        let shadowRoot = this.attachShadow({ mode: "closed" });

        shadowRoot.innerHTML = `
        <style>
            :host {
                display: block;
            }

            :host([role]:not([aria-disabled="true"])) {
                cursor: pointer;
            }

            :host(:focus-visible) {
                outline: 2px solid var(--focus-color, Highlight);
                outline-offset: 2px;
            }
        </style>
        <slot></slot>
        `;

        this.onClick = this.onClick.bind(this);
        this.onKeyPress = this.onKeyPress.bind(this);
    }

    public set onPress(
        onPress: ((event: PointerEvent | KeyboardEvent) => void) | null
    ) {
        this._onPress = onPress;

        if (onPress === null) {
            this.removeEventListener("click", this.onClick);
            this.removeEventListener("keypress", this.onKeyPress);

            // Only remove the default "button" role, not a custom one
            if (this._customRole === null) {
                this.removeAttribute("role");
            }
            this.removeAttribute("tabindex");
        } else {
            this.addEventListener("click", this.onClick);
            this.addEventListener("keypress", this.onKeyPress);

            if (this._customRole === null) {
                this.role = "button";
            }
            this.setAttribute("tabindex", "0"); // Make it focusable
        }
    }

    public set isSensitive(isSensitive: boolean) {
        this._isSensitive = isSensitive;
        this.ariaDisabled = isSensitive ? "false" : "true";
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
        if (this._onPress !== null && this._isSensitive) {
            this._onPress(event);
        }
    }
}

customElements.define("rio-pressable-element", PressableElement);
