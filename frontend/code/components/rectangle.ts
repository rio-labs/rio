import { Color, ComponentId, AnyFill } from "../dataModels";
import { colorToCssString, fillToCss } from "../cssUtils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { RippleEffect } from "../rippleEffect";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type RectangleState = ComponentState & {
    _type_: "Rectangle-builtin";
    content: ComponentId | null;
    transition_time: number;
    cursor: string;
    ripple: boolean;

    fill: AnyFill;
    stroke_color: Color;
    stroke_width: number;
    corner_radius: [number, number, number, number];
    shadow_color: Color;
    shadow_radius: number;
    shadow_offset_x: number;
    shadow_offset_y: number;

    hover_fill: AnyFill | null;
    hover_stroke_color: Color | null;
    hover_stroke_width: number | null;
    hover_corner_radius: [number, number, number, number] | null;
    hover_shadow_color: Color | null;
    hover_shadow_radius: number | null;
    hover_shadow_offset_x: number | null;
    hover_shadow_offset_y: number | null;
};

function numberToRem(num: number): string {
    return `${num}rem`;
}

// Functions that convert an attribute of `RectangleState` to CSS. The return
// value can either be a string or an object of `{cssProperty: cssValue}`.
const JS_TO_CSS_VALUE: {
    [attr: string]: (value: any) => string | { [attr: string]: string };
} = {
    fill: fillToCss,
    stroke_color: colorToCssString,
    stroke_width: numberToRem,
    corner_radius: (radii: [number, number, number, number]) =>
        radii.map((num) => `${num}rem`).join(" "),
    shadow_color: colorToCssString,
    shadow_radius: numberToRem,
    shadow_offset_x: numberToRem,
    shadow_offset_y: numberToRem,
};

function cursorToCSS(cursor: string): string {
    const CURSOR_MAP = {
        default: "auto",
        none: "none",
        help: "help",
        pointer: "pointer",
        loading: "wait",
        "background-loading": "progress",
        crosshair: "crosshair",
        text: "text",
        move: "move",
        "not-allowed": "not-allowed",
        "can-grab": "grab",
        grabbed: "grabbing",
        "zoom-in": "zoom-in",
        "zoom-out": "zoom-out",
        // These values are from the deprecated CursorStyle enum
        notAllowed: "not-allowed",
        isGrabbed: "grabbing",
        zoomIn: "zoom-in",
        zoomOut: "zoom-out",
        canGrab: "grab",
        backgroundLoading: "progress",
    };

    console.assert(cursor in CURSOR_MAP, `Unknown cursor: ${cursor}`);
    return CURSOR_MAP[cursor];
}

export class RectangleComponent extends ComponentBase<RectangleState> {
    // If this rectangle has a ripple effect, this is the ripple instance.
    // `null` otherwise.
    private rippleInstance: RippleEffect | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-rectangle");
        return element;
    }

    updateElement(
        deltaState: DeltaState<RectangleState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(context, deltaState.content);

        if (deltaState.transition_time !== undefined) {
            this.element.style.transitionDuration = `${deltaState.transition_time}s`;
        }

        if (deltaState.cursor !== undefined) {
            this.element.style.cursor = cursorToCSS(deltaState.cursor);
        }

        if (deltaState.ripple === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(this.element);
            }
        } else if (deltaState.ripple === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;
            }
        }

        // Apply all the styling properties
        for (let [attrName, js_to_css] of Object.entries(JS_TO_CSS_VALUE)) {
            let value = deltaState[attrName];
            if (value !== undefined && value !== null) {
                let cssValues = js_to_css(value);
                if (typeof cssValues === "string") {
                    cssValues = { [attrName]: cssValues };
                }

                for (let [prop, val] of Object.entries(cssValues)) {
                    this.element.style.setProperty(
                        `--rio-rectangle-${prop}`,
                        val
                    );
                }
            }

            let hoverValue = deltaState["hover_" + attrName];
            if (hoverValue !== undefined) {
                if (hoverValue === null) {
                    // No hover value? Use the corresponding non-hover value
                    if (value !== undefined && value !== null) {
                        let cssValues = js_to_css(value);
                        if (typeof cssValues === "string") {
                            cssValues = { [attrName]: cssValues };
                        }

                        for (let [prop, val] of Object.entries(cssValues)) {
                            this.element.style.setProperty(
                                `--rio-rectangle-hover-${prop}`,
                                `var(--rio-rectangle-${prop})`
                            );
                        }
                    }
                } else {
                    let cssValues = js_to_css(hoverValue);
                    if (typeof cssValues === "string") {
                        cssValues = { [attrName]: cssValues };
                    }

                    for (let [prop, val] of Object.entries(cssValues)) {
                        this.element.style.setProperty(
                            `--rio-rectangle-hover-${prop}`,
                            val
                        );
                    }
                }
            }
        }
    }
}
