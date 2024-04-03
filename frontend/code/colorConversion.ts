export function hsvToRgb(
    h: number,
    s: number,
    v: number
): [number, number, number] {
    let i = Math.floor(h / 60);
    let f = h / 60 - i;
    let p = v * (1 - s);
    let q = v * (1 - f * s);
    let t = v * (1 - (1 - f) * s);

    let r, g, b;

    switch (i % 6) {
        case 0:
            (r = v), (g = t), (b = p);
            break;

        case 1:
            (r = q), (g = v), (b = p);
            break;

        case 2:
            (r = p), (g = v), (b = t);
            break;

        case 3:
            (r = p), (g = q), (b = v);
            break;

        case 4:
            (r = t), (g = p), (b = v);
            break;

        case 5:
            (r = v), (g = p), (b = q);
            break;
    }

    return [r, g, b];
}

export function rgbToHsv(
    r: number,
    g: number,
    b: number
): [number, number, number] {
    let max = Math.max(r, g, b);
    let min = Math.min(r, g, b);

    let d = max - min;
    let s = max === 0 ? 0 : d / max;

    let h;

    switch (max) {
        case min:
            h = 0;
            break;
        case r:
            h = g - b + d * (g < b ? 6 : 0);
            h /= 6 * d;
            break;
        case g:
            h = b - r + d * 2;
            h /= 6 * d;
            break;
        case b:
            h = r - g + d * 4;
            h /= 6 * d;
            break;
    }

    return [h * 360, s, max];
}

export function rgbToHex(r: number, g: number, b: number): string {
    // Convert the float values to their hexadecimal counterparts
    const rHex = Math.floor(r * 255)
        .toString(16)
        .padStart(2, '0');
    const gHex = Math.floor(g * 255)
        .toString(16)
        .padStart(2, '0');
    const bHex = Math.floor(b * 255)
        .toString(16)
        .padStart(2, '0');

    // Combine them into a hex color string
    return `${rHex}${gHex}${bHex}`;
}

export function rgbaToHex(r: number, g: number, b: number, a: number): string {
    // Convert the float values to their hexadecimal counterparts
    const rHex = Math.floor(r * 255)
        .toString(16)
        .padStart(2, '0');
    const gHex = Math.floor(g * 255)
        .toString(16)
        .padStart(2, '0');
    const bHex = Math.floor(b * 255)
        .toString(16)
        .padStart(2, '0');
    const aHex = Math.floor(a * 255)
        .toString(16)
        .padStart(2, '0');

    // Combine them into a hex color string
    return `${rHex}${gHex}${bHex}${aHex}`;
}
