import { pixelsPerRem } from './app';
import { textStyleToCss } from './cssUtils';
import { TextStyle } from './dataModels';

const _textDimensionsCache = new Map<string, [number, number]>();

let cacheHits: number = 0;
let cacheMisses: number = 0;

/// Returns the width and height of the given text in pixels. Does not cache
/// the result.
export function getTextDimensions(
    text: string,
    style: 'heading1' | 'heading2' | 'heading3' | 'text' | 'dim' | TextStyle,
    restrictWidth: number | null = null
): [number, number] {
    // Make sure the text isn't just whitespace, as that results in a wrong [0,
    // 0]
    //
    // FIXME: Still imperfect, as now all whitespace is the same width, and an
    // empty string has a width.
    if (text.trim().length === 0) {
        text = 'l';
    }

    // Build a key for the cache
    let key: string;
    let sizeNormalizationFactor: number;
    if (typeof style === 'string') {
        key = `${style}+${text}`;
        sizeNormalizationFactor = 1;
    } else {
        key = `${style.fontName}+${style.fontWeight}+${style.italic}+${style.underlined}+${style.allCaps}+${text}`;
        sizeNormalizationFactor = style.fontSize;
    }

    // Restrict the width?
    if (restrictWidth !== null) {
        key += `+${restrictWidth}`;
    }

    // Display cache statistics
    // if (cacheHits + cacheMisses > 0) {
    //     console.log(`Cache hit rate: ${cacheHits / (cacheHits + cacheMisses)}`);
    // }

    // Check the cache
    let cached = _textDimensionsCache.get(key);

    if (cached !== undefined) {
        cacheHits++;
        return [
            cached[0] * sizeNormalizationFactor,
            cached[1] * sizeNormalizationFactor,
        ];
    }
    cacheMisses++;

    // Spawn an element to measure the text
    let element = document.createElement('div');
    element.textContent = text;
    Object.assign(element.style, textStyleToCss(style));
    element.style.position = 'absolute';
    element.style.whiteSpace = 'pre-wrap'; // Required for multi-line text
    document.body.appendChild(element);

    if (restrictWidth !== null) {
        element.style.width = `${restrictWidth}rem`;
    }

    let rect = element.getBoundingClientRect();
    let result = [rect.width / pixelsPerRem, rect.height / pixelsPerRem] as [
        number,
        number,
    ];
    element.remove();

    // Store in the cache and return
    _textDimensionsCache.set(key, [
        result[0] / sizeNormalizationFactor,
        result[1] / sizeNormalizationFactor,
    ]);
    return result;
}

globalThis.getTextDimensions = getTextDimensions; // For debugging

/// Get the width and height an element takes up on the screen, in rems.
///
/// This works even if the element is not visible, e.g. because a parent is
/// hidden.
export function getElementDimensions(element: HTMLElement): [number, number] {
    // Remember everything necessary to restore the original state
    let isInDom = element.isConnected;
    let originalDisplay = element.style.display;

    let parentElement: HTMLElement | null = null;
    let nextSibling: Node | null = null;
    if (!isInDom) {
        parentElement = element.parentElement;
        nextSibling = element.nextSibling;
    }

    // Ensure the element is in the DOM
    if (!isInDom) {
        document.body.appendChild(element);
    } else {
        element.style.display = 'fixed';
    }

    // Get its dimensions
    let result = [
        element.scrollWidth / pixelsPerRem,
        element.scrollHeight / pixelsPerRem,
    ] as [number, number];

    // Restore the original state
    if (isInDom) {
        element.style.display = originalDisplay;
    } else if (parentElement === null) {
        element.remove();
    } else if (nextSibling === null) {
        parentElement.appendChild(element);
    } else {
        parentElement.insertBefore(element, nextSibling);
    }

    return result;
}

globalThis.getElementDimensions = getElementDimensions; // For debugging

export function getElementWidth(element: HTMLElement): number {
    // TODO: Don't request both height and width - that's the whole point of
    // this function
    let dimensions = getElementDimensions(element);
    return dimensions[0];
}

export function getElementHeight(element: HTMLElement): number {
    // TODO: Don't request both height and width - that's the whole point of
    // this function
    let dimensions = getElementDimensions(element);
    return dimensions[1];
}
