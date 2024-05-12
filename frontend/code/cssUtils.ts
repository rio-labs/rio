import { Color, Fill, TextStyle } from './dataModels';

export function colorToCssString(color: Color): string {
    const [r, g, b, a] = color;
    return `rgba(${r * 255}, ${g * 255}, ${b * 255}, ${a})`;
}

function gradientToCssString(
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
        ', '
    )})`;
}

export function fillToCssString(fill: Fill): string {
    // Solid Color
    if (fill.type === 'solid') {
        return colorToCssString(fill.color);
    }

    // Linear Gradient
    else if (fill.type === 'linearGradient') {
        if (fill.stops.length == 1) {
            return colorToCssString(fill.stops[0][0]);
        }

        return gradientToCssString(fill.angleDegrees, fill.stops);
    }

    // Image
    else if (fill.type === 'image') {
        let cssUrl = `url('${fill.imageUrl}')`;

        if (fill.fillMode == 'fit') {
            return `${cssUrl} center/contain no-repeat`;
        } else if (fill.fillMode == 'stretch') {
            return `${cssUrl} top left / 100% 100%`;
        } else if (fill.fillMode == 'tile') {
            return `${cssUrl} left top repeat`;
        } else if (fill.fillMode == 'zoom') {
            return `${cssUrl} center/cover no-repeat`;
        } else {
            // Invalid fill mode
            // @ts-ignore
            throw `Invalid fill mode for image fill: ${fill.type}`;
        }
    }

    // Invalid fill type
    // @ts-ignore
    throw `Invalid fill type: ${fill.type}`;
}

export function fillToCss(fill: Fill): { background: string } {
    return {
        background: fillToCssString(fill),
    };
}

export function textStyleToCss(
    style: 'heading1' | 'heading2' | 'heading3' | 'text' | 'dim' | TextStyle
): {
    'font-family': string;
    'font-size': string;
    'font-weight': string;
    'font-style': string;
    'text-decoration': string;
    'text-transform': string;
    color: string;
    background: string;
    '-webkit-background-clip': string;
    '-webkit-text-fill-color': string;
    opacity: string;
} {
    let fontFamily: string;
    let fontSize: string;
    let fontWeight: string;
    let fontStyle: string;
    let textDecoration: string;
    let textTransform: string;
    let color: string;
    let background: string;
    let backgroundClip: string;
    let textFillColor: string;
    let opacity: string;

    // `Dim` is the same as `text`, just with some opacity
    if (style === 'dim') {
        style = 'text';
        opacity = '0.4';
    } else {
        opacity = '1';
    }

    // Predefined style from theme
    if (typeof style === 'string') {
        let globalPrefix = `var(--rio-global-${style}-`;
        let localPrefix = `var(--rio-local-${style}-`;

        // Text fill
        color = localPrefix + 'color)';
        background = localPrefix + 'background)';
        backgroundClip = localPrefix + 'background-clip)';
        textFillColor = localPrefix + 'fill-color)';

        // Font weight. This is local so that buttons can make their label text
        // bold.
        fontWeight = localPrefix + 'font-weight)';

        // Others
        fontFamily = globalPrefix + 'font-name)';
        fontSize = globalPrefix + 'font-size)';
        fontStyle = globalPrefix + 'font-italic)';
        textDecoration = globalPrefix + 'underlined)';
        textTransform = globalPrefix + 'all-caps)';
    }

    // Explicitly defined style
    else {
        fontSize = style.fontSize + 'em';
        fontStyle = style.italic ? 'italic' : 'normal';
        fontWeight = style.fontWeight;
        textDecoration = style.underlined ? 'underline' : 'none';
        textTransform = style.allCaps ? 'uppercase' : 'none';

        // If no font family is provided, stick to the theme's.
        if (style.fontName === null) {
            fontFamily = 'inherit';
        } else {
            fontFamily = style.fontName;
        }

        // If no fill is provided, stick to the local text color. This allows
        // the user to have their text automatically adapt to different
        // themes/contexts.
        if (style.fill === null) {
            color = 'var(--rio-local-text-color)';
            background = 'var(--rio-local-text-background)';
            backgroundClip = 'var(--rio-local-text-background-clip)';
            textFillColor = 'var(--rio-local-text-fill-color)';
        }
        // Color?
        else if (Array.isArray(style.fill)) {
            color = colorToCssString(style.fill);
            background = 'none';
            backgroundClip = 'unset';
            textFillColor = 'unset';
        }
        // Solid fill, i.e. also a color
        else if (style.fill.type === 'solid') {
            color = colorToCssString(style.fill.color);
            background = 'none';
            backgroundClip = 'unset';
            textFillColor = 'unset';
        }
        // Anything else
        else {
            color = 'unset';
            background = fillToCssString(style.fill);
            backgroundClip = 'text';
            textFillColor = 'transparent';
        }
    }

    return {
        'font-family': fontFamily,
        'font-size': fontSize,
        'font-weight': fontWeight,
        'font-style': fontStyle,
        'text-decoration': textDecoration,
        'text-transform': textTransform,
        color: color,
        background: background,
        '-webkit-background-clip': backgroundClip,
        '-webkit-text-fill-color': textFillColor,
        opacity: opacity,
    };
}
