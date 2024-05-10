import { Color, ColorSet, Fill } from './dataModels';
import { colorToCssString } from './cssUtils';

const ICON_PROMISE_CACHE: { [key: string]: Promise<string> } = {};

/// Removes any switcheroos from the given element
function removeSwitcheroos(element: HTMLElement): void {
    element.classList.remove(
        'rio-switcheroo-background',
        'rio-switcheroo-neutral',
        'rio-switcheroo-hud',
        'rio-switcheroo-primary',
        'rio-switcheroo-secondary',
        'rio-switcheroo-success',
        'rio-switcheroo-warning',
        'rio-switcheroo-danger',
        'rio-switcheroo-disabled',
        'rio-switcheroo-custom',
        'rio-switcheroo-bump'
    );
}

export function applySwitcheroo(
    element: HTMLElement,
    colorSet: ColorSet | 'bump'
): void {
    // Remove any preexisting switcheroos
    removeSwitcheroos(element);

    // If no color set is desired don't apply any new one
    if (colorSet === 'keep') {
        return;
    }

    // Is this a well-known switcheroo?
    if (typeof colorSet === 'string') {
        element.classList.add(`rio-switcheroo-${colorSet}`);
        return;
    }

    // Custom color sets need additional variables to be defined
    element.style.setProperty(
        '--rio-custom-local-bg',
        colorToCssString(colorSet.localBg)
    );
    element.style.setProperty(
        '--rio-custom-local-bg-variant',
        colorToCssString(colorSet.localBgVariant)
    );
    element.style.setProperty(
        '--rio-custom-local-bg-active',
        colorToCssString(colorSet.localBgActive)
    );
    element.style.setProperty(
        '--rio-custom-local-fg',
        colorToCssString(colorSet.localFg)
    );

    // Apply the switcheroo
    element.classList.add('rio-switcheroo-custom');
}

export function applyFillToSVG(svgRoot: SVGSVGElement, fill: Fill): void {
    switch (fill.type) {
        case 'solid':
            applySolidFill(svgRoot, fill.color);
            break;

        case 'linearGradient':
            applyLinearGradientFill(svgRoot, fill.angleDegrees, fill.stops);
            break;

        case 'image':
            applyImageFill(svgRoot, fill.imageUrl, fill.fillMode);
            break;

        default:
            throw new Error(`Invalid fill type: ${fill}`);
    }
}

function applySolidFill(svgRoot: SVGSVGElement, color: Color): void {
    const [r, g, b, a] = color;
    svgRoot.style.fill = `rgba(${r * 255}, ${g * 255}, ${b * 255}, ${a})`;
}

function applyLinearGradientFill(
    svgRoot: SVGSVGElement,
    angleDegrees: number,
    stops: [Color, number][]
): void {
    // Create a new linear gradient
    const gradientId = generateUniqueId();
    const gradient = createLinearGradient(gradientId, angleDegrees, stops);

    // Add it to the "defs" section of the SVG
    let defs = svgRoot.querySelector('defs');

    if (defs === null) {
        defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        svgRoot.appendChild(defs);
    }

    defs.appendChild(gradient);

    // Add the gradient to the path
    svgRoot.style.fill = `url(#${gradientId})`;
}

function applyImageFill(
    svgRoot: SVGSVGElement,
    imageUrl: string,
    fillMode: 'fit' | 'stretch' | 'tile' | 'zoom'
): void {
    // Create a pattern
    const patternId = generateUniqueId();
    const pattern = document.createElementNS(
        'http://www.w3.org/2000/svg',
        'pattern'
    );
    pattern.setAttribute('id', patternId);
    pattern.setAttribute('width', '100%');
    pattern.setAttribute('height', '100%');
    pattern.setAttribute('preserveAspectRatio', 'none');

    // Create an image
    const image = document.createElementNS(
        'http://www.w3.org/2000/svg',
        'image'
    );
    image.setAttribute('width', '100%');
    image.setAttribute('height', '100%');
    image.setAttribute('href', imageUrl);
    image.setAttribute('preserveAspectRatio', 'none');
    pattern.appendChild(image);

    // Add the pattern to the "defs" section of the SVG
    let defs = svgRoot.querySelector('defs');

    if (defs === null) {
        defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        svgRoot.appendChild(defs);
    }

    defs.appendChild(pattern);

    // Apply the pattern to the path
    svgRoot.setAttribute('fill', `url(#${patternId})`);
}

function generateUniqueId(): string {
    return Math.random().toString(36);
}

function createLinearGradient(
    gradientId: string,
    angleDegrees: number,
    stops: [Color, number][]
): SVGLinearGradientElement {
    const gradient = document.createElementNS(
        'http://www.w3.org/2000/svg',
        'linearGradient'
    );
    gradient.setAttribute('id', gradientId);
    gradient.setAttribute('gradientTransform', `rotate(${angleDegrees})`);

    let ii = -1;
    for (const [color, offset] of stops) {
        ii += 1;

        const [r, g, b, a] = color;
        const stop = document.createElementNS(
            'http://www.w3.org/2000/svg',
            'stop'
        );

        stop.setAttribute('offset', `${offset}`);
        stop.setAttribute(
            'style',
            `stop-color: rgba(${r * 255}, ${g * 255}, ${b * 255}, ${a})`
        );
        stop.setAttribute('id', `${gradientId}-stop-${ii}`);
        gradient.appendChild(stop);
    }

    return gradient;
}

export async function applyIcon(
    target: HTMLElement,
    iconName: string,
    cssColor: string
): Promise<void> {
    // Is the icon already in the cache?
    let promise = ICON_PROMISE_CACHE[iconName];

    // No, load it from the server
    if (promise === undefined) {
        console.log(`Fetching icon ${iconName} from server`);

        promise = fetch(`/rio/icon/${iconName}`).then((response) =>
            response.text()
        );

        ICON_PROMISE_CACHE[iconName] = promise;
    }

    // Avoid races: When calling this function multiple times on the same
    // element it can sometimes assign the first icon AFTER the second one, thus
    // ending up with the wrong icon in the end.
    //
    // To avoid this, assign the icon that's supposed to be loaded into the HTML
    // element as a data attribute. Once the icon's source has been fetched,
    // only apply it if the data attribute still matches the icon name.
    target.setAttribute('data-rio-icon', iconName);

    // Await the future
    let svgSource: string;
    try {
        svgSource = await promise;
    } catch (err) {
        console.error(`Error loading icon ${iconName}: ${err}`);
        delete ICON_PROMISE_CACHE[iconName];
        return;
    }

    // Check if the icon is still needed
    if (target.getAttribute('data-rio-icon') !== iconName) {
        return;
    }
    target.removeAttribute('data-rio-icon');

    // Apply the icon
    target.innerHTML = svgSource;

    // Apply the color
    let svgRoot = target.querySelector('svg') as SVGSVGElement;
    svgRoot.style.fill = cssColor;
}
