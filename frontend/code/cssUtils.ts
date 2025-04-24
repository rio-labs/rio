import { Color, AnyFill, TextStyle, TextCompatibleFill } from "./dataModels";

export function colorToCssString(color: Color): string {
    const [r, g, b, a] = color;
    return `rgba(${r * 255}, ${g * 255}, ${b * 255}, ${a})`;
}

function linearGradientToCssString(
    angleDegrees: number,
    stops: [Color, number][]
): string {
    let stopStrings: string[] = [];

    for (let i = 0; i < stops.length; i++) {
        let color = stops[i][0];
        let position = stops[i][1];
        stopStrings.push(`${colorToCssString(color)} ${position * 100}%`);
    }

    return `linear-gradient(${90 - angleDegrees}deg, ${stopStrings.join(
        ", "
    )})`;
}

function radialGradientToCssString(
    centerX: number,
    centerY: number,
    stops: [Color, number][]
): string {
    let stopStrings: string[] = [];

    for (let i = 0; i < stops.length; i++) {
        let color = stops[i][0];
        let position = stops[i][1];
        stopStrings.push(`${colorToCssString(color)} ${position * 100}%`);
    }

    const centerPosition = `${centerX * 100}% ${centerY * 100}%`;
    return `radial-gradient(circle at ${centerPosition}, ${stopStrings.join(
        ", "
    )})`;
}

export function fillToCss(fill: AnyFill): {
    background: string;
    "backdrop-filter": string;
} {
    let background: string;
    let backdropFilter: string = "none";

    switch (fill.type) {
        // Solid Color
        case "solid":
            background = colorToCssString(fill.color);
            break;

        // Linear Gradient
        //
        // Note: Python already ensures that there are at least two stops, and
        // that the first one is at 0 and the last one is at 1. No need to
        // verify any of that here.
        case "linearGradient":
            background = linearGradientToCssString(
                fill.angleDegrees,
                fill.stops
            );
            break;

        // Radial Gradient
        case "radialGradient":
            background = radialGradientToCssString(
                fill.centerX,
                fill.centerY,
                fill.stops
            );
            break;

        // Image
        case "image":
            const cssUrl = `url('${fill.imageUrl}')`;
            switch (fill.fillMode) {
                case "fit":
                    background = `${cssUrl} center/contain no-repeat`;
                    break;
                case "stretch":
                    background = `${cssUrl} top left / 100% 100%`;
                    break;
                case "zoom":
                    background = `${cssUrl} center/cover no-repeat`;
                    break;
                case "tile":
                    background = `${cssUrl} top left / ${fill.tileSize[0]}rem ${fill.tileSize[1]}rem repeat`;
                    break;
                default:
                    // Invalid fill mode
                    // @ts-ignore
                    throw `Invalid fill mode for image fill: ${fill.type}`;
            }
            break;

        // Frosted Glass
        case "frostedGlass":
            background = colorToCssString(fill.color);
            backdropFilter = `blur(${fill.blurSize}rem)`;
            break;

        default:
            // Invalid fill type
            // @ts-ignore
            throw `Invalid fill type: ${fill.type}`;
    }

    return {
        background: background,
        "backdrop-filter": backdropFilter,
    };
}

type TextFillCss = {
    color: string;
    background: string;
    "-webkit-background-clip": string;
    "-webkit-text-fill-color": string;
};

export function textfillToCss(fill: TextCompatibleFill): TextFillCss {
    // If no fill is provided, stick to the local text color. This allows
    // the user to have their text automatically adapt to different
    // themes/contexts.
    if (fill === null) {
        return {
            color: "var(--rio-local-text-color)",
            background: "var(--rio-local-text-background)",
            "-webkit-background-clip": "var(--rio-local-text-background-clip)",
            "-webkit-text-fill-color": "var(--rio-local-text-fill-color)",
        };
    }

    // Color?
    if (Array.isArray(fill)) {
        return {
            color: colorToCssString(fill),
            background: "none",
            "-webkit-background-clip": "unset",
            "-webkit-text-fill-color": "unset",
        };
    }

    // Solid fill, i.e. also a color
    if (fill.type === "solid") {
        return {
            color: colorToCssString(fill.color),
            background: "none",
            "-webkit-background-clip": "unset",
            "-webkit-text-fill-color": "unset",
        };
    }

    // Anything else
    return {
        color: "unset",
        background: fillToCss(fill).background,
        // TODO: The `backdrop-filter` in `cssProps` is ignored because it
        // doesn't do what we want. (It isn't clipped to the text, it blurs
        // everything behind the element.) This means FrostedGlassFill
        // doesn't blur the background when used on text.
        "-webkit-background-clip": "text",
        "-webkit-text-fill-color": "transparent",
    };
}

type TextStyleCss = {
    opacity?: string;
    "font-family"?: string;
    "font-size"?: string;
    "font-weight"?: string;
    "font-style"?: string;
    "text-decoration"?: string;
    "text-transform"?: string;
} & Partial<TextFillCss>;

export function textStyleToCss(
    style: "heading1" | "heading2" | "heading3" | "text" | "dim" | TextStyle
): TextStyleCss {
    let result: TextStyleCss = {};

    // `Dim` is the same as `text`, just with some opacity
    if (style === "dim") {
        style = "text";
        result.opacity = "0.4";
    }

    // Predefined style from theme
    if (typeof style === "string") {
        let globalPrefix = `var(--rio-global-${style}-`;
        let localPrefix = `var(--rio-local-${style}-`;

        // Text fill
        result.color = localPrefix + "color)";
        result.background = localPrefix + "background)";
        result["-webkit-background-clip"] = localPrefix + "background-clip)";
        result["-webkit-text-fill-color"] = localPrefix + "fill-color)";

        // Font weight. This is local so that buttons can make their label text
        // bold.
        result["font-weight"] = localPrefix + "font-weight)";

        // Others
        result["font-family"] = globalPrefix + "font-name)";
        result["font-size"] = globalPrefix + "font-size)";
        result["font-style"] = globalPrefix + "font-style)";
        result["text-decoration"] = globalPrefix + "text-decoration)";
        result["text-transform"] = globalPrefix + "all-caps)";
    }

    // Explicitly defined style
    else {
        if (style.fontName !== null) {
            result["font-family"] = style.fontName;
        }

        if (style.fontSize !== null) {
            result["font-size"] = style.fontSize + "rem";
        }

        if (style.fontWeight !== null) {
            result["font-weight"] = style.fontWeight;
        }

        if (style.italic !== null) {
            result["font-style"] = style.italic ? "italic" : "normal";
        }

        // TODO: `underlined` and `strikethrough` both map to the
        // `text-decoration` CSS attribute. Which means that if only one of them
        // is defined, the other one will be disabled instead of inherited. I
        // don't think we can do anything about that, though.
        if (style.underlined !== null || style.strikethrough !== null) {
            let textDecorations: string[] = [];

            if (style.underlined) {
                textDecorations.push("underline");
            }

            if (style.strikethrough) {
                textDecorations.push("line-through");
            }

            result["text-decoration"] = textDecorations.join(" ");
        }

        if (style.allCaps !== null) {
            result["text-transform"] = style.allCaps ? "uppercase" : "none";
        }

        if (style.fill !== null) {
            Object.assign(result, textfillToCss(style.fill));
        }
    }

    return result;
}

export function applyTextStyleCss(
    element: HTMLElement,
    cssProps: TextStyleCss
): void {
    // Since TextStyles don't have to include all of the styling parameters, we
    // have to clear the old style before applying the new one to ensure that no
    // undesired settings remain.
    removeTextStyle(element);
    Object.assign(element.style, cssProps);
}

export function removeTextStyle(element: HTMLElement): void {
    for (let attribute of [
        "opacity",
        "font-family",
        "font-size",
        "font-weight",
        "font-style",
        "text-decoration",
        "text-transform",
        "color",
        "background",
        "-webkit-background-clip",
        "-webkit-text-fill-color",
    ]) {
        element.style.removeProperty(attribute);
    }
}
