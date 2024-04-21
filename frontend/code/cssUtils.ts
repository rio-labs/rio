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
    'text-style': string;
    'text-decoration': string;
    'text-transform': string;
    color: string;
    background: string;
    '-webkit-background-clip': string;
    '-webkit-text-fill-color': string;
} {
    let result = {
        background: 'none',
        color: 'unset', // FIXME
    };

    // `Dim` is the same as `text`, just with some opacity
    if (style === 'dim') {
        style = 'text';
        result['opacity'] = '0.4';
    } else {
        result['opacity'] = '1';
    }

    // Predefined style from theme
    if (typeof style === 'string') {
        let globalPrefix = `var(--rio-global-${style}-`;
        let localPrefix = `var(--rio-local-${style}-`;

        // Text fill
        result['color'] = localPrefix + 'color)';
        result['background'] = localPrefix + 'background)';
        result['-webkit-background-clip'] = localPrefix + 'background-clip)';
        result['-webkit-text-fill-color'] = localPrefix + 'fill-color)';

        // Font weight. This is local, so that buttons can make their label text
        // be bold.
        result['font-weight'] = localPrefix + 'font-weight)';

        // Others
        result['font-family'] = globalPrefix + 'font-name)';
        result['font-size'] = globalPrefix + 'font-size)';
        result['text-style'] = globalPrefix + 'font-italic)';
        result['text-decoration'] = globalPrefix + 'underlined)';
        result['text-transform'] = globalPrefix + 'all-caps)';
    }

    // Explicitly defined style
    else {
        result['font-size'] = style.fontSize + 'em';
        result['font-style'] = style.italic ? 'italic' : 'normal';
        result['font-weight'] = style.fontWeight;
        result['text-decoration'] = style.underlined ? 'underline' : 'none';
        result['text-transform'] = style.allCaps ? 'uppercase' : 'none';

        // If no font family is provided, stick to the theme's.
        if (style.fontName === null) {
            result['font-family'] = 'inherit';
        } else {
            result['font-family'] = style.fontName;
        }

        // If no fill is provided, stick to the local text color. This allows
        // the user to have their text automatically adapt to different
        // themes/contexts.
        if (style.fill === null) {
            result['color'] = 'var(--rio-local-text-color)';
            result['background'] = 'var(--rio-local-text-background)';
            result['-webkit-background-clip'] =
                'var(--rio-local-text-background-clip)';
            result['-webkit-text-fill-color'] =
                'var(--rio-local-text-fill-color)';
        }
        // Color?
        else if (Array.isArray(style.fill)) {
            result['color'] = colorToCssString(style.fill);
            result['background'] = 'none';
            result['-webkit-background-clip'] = 'unset';
            result['-webkit-text-fill-color'] = 'unset';
        }
        // Solid fill, i.e. also a color
        else if (style.fill.type === 'solid') {
            result['color'] = colorToCssString(style.fill.color);
            result['background'] = 'none';
            result['-webkit-background-clip'] = 'unset';
            result['-webkit-text-fill-color'] = 'unset';
        }
        // Anything else
        else {
            result['color'] = 'unset';
            result['background'] = fillToCssString(style.fill);
            result['-webkit-background-clip'] = 'text';
            result['-webkit-text-fill-color'] = 'transparent';
        }
    }

    // @ts-ignore
    return result;
}
