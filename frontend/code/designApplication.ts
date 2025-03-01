import {
    COLOR_SET_NAMES,
    Color,
    ColorSet,
    ColorSetName,
    ImageFill,
    LinearGradientFill,
    RadialGradientFill,
    SolidFill,
} from "./dataModels";
import { colorToCssString } from "./cssUtils";

/// Removes any switcheroos from the given element
function removeSwitcheroos(element: HTMLElement): void {
    element.classList.remove(
        "rio-switcheroo-background",
        "rio-switcheroo-neutral",
        "rio-switcheroo-hud",
        "rio-switcheroo-primary",
        "rio-switcheroo-secondary",
        "rio-switcheroo-success",
        "rio-switcheroo-warning",
        "rio-switcheroo-danger",
        "rio-switcheroo-disabled",
        "rio-switcheroo-custom",
        "rio-switcheroo-bump"
    );
}

export function applySwitcheroo(
    element: HTMLElement,
    colorSet: ColorSet | "bump"
): void {
    // Remove any preexisting switcheroos
    removeSwitcheroos(element);

    // If no color set is desired don't apply any new one
    if (colorSet === "keep") {
        return;
    }

    // Is this a well-known switcheroo?
    if (typeof colorSet === "string") {
        element.classList.add(`rio-switcheroo-${colorSet}`);
        return;
    }

    // Custom color sets need additional variables to be defined
    element.style.setProperty(
        "--rio-custom-local-bg",
        colorToCssString(colorSet.localBg)
    );
    element.style.setProperty(
        "--rio-custom-local-bg-variant",
        colorToCssString(colorSet.localBgVariant)
    );
    element.style.setProperty(
        "--rio-custom-local-bg-active",
        colorToCssString(colorSet.localBgActive)
    );
    element.style.setProperty(
        "--rio-custom-local-fg",
        colorToCssString(colorSet.localFg)
    );

    // Apply the switcheroo
    element.classList.add("rio-switcheroo-custom");
}

export function applyFillToSVG(
    svgRoot: SVGSVGElement,
    fillLike:
        | SolidFill
        | LinearGradientFill
        | RadialGradientFill
        | ImageFill
        | Color
        | ColorSet
        | "dim"
        | string // A CSS color value
): void {
    // The svg element may already have a fill, so we must make sure that every
    // fill overwrites every other fill's style properties.
    let styleFill: string;
    let opacity: string = "1";

    // Case: No fill was provided, so use the default foreground color
    if (fillLike === "keep") {
        styleFill = "var(--rio-local-text-color)";
    }
    // Case: "dim". This is a special case, which is represented by also using
    // the foreground color, but with a reduced opacity.
    else if (fillLike === "dim") {
        styleFill = "var(--rio-local-text-color)";
        opacity = "0.4";
    } else if (typeof fillLike === "string") {
        // Case: Well known, predefined colorset.
        //
        // Note that this uses the background rather than foreground color. The
        // foreground is intended to be used if the background was already set to
        // background color.
        if (COLOR_SET_NAMES.includes(fillLike as ColorSetName)) {
            styleFill = `var(--rio-global-${fillLike}-bg)`;
        }
        // Case: CSS color value
        else {
            styleFill = fillLike;
        }
    }
    // Case: single color
    else if (Array.isArray(fillLike)) {
        styleFill = colorToCssString(fillLike);
    }
    // Case: Colorset
    else if (fillLike["localBg"] !== undefined) {
        // @ts-ignore
        styleFill = colorToCssString(fillLike.localBg);
    }
    // Case: Actual Fill object
    else {
        fillLike = fillLike as
            | SolidFill
            | LinearGradientFill
            | RadialGradientFill
            | ImageFill;

        switch (fillLike.type) {
            case "solid":
                styleFill = colorToCssString(fillLike.color);
                break;

            case "linearGradient":
                styleFill = createLinearGradientFillAndReturnFill(
                    svgRoot,
                    fillLike.angleDegrees,
                    fillLike.stops
                );
                break;

            case "radialGradient":
                styleFill = createRadialGradientFillAndReturnFill(
                    svgRoot,
                    fillLike.centerX,
                    fillLike.centerY,
                    fillLike.stops
                );
                break;

            case "image":
                styleFill = createImageFillAndReturnFill(
                    svgRoot,
                    fillLike.imageUrl,
                    fillLike.fillMode,
                    fillLike.tileSize
                );
                break;

            default:
                throw new Error(`Invalid fill type: ${fillLike}`);
        }
    }

    svgRoot.style.fill = styleFill;
    svgRoot.style.opacity = opacity;
}

function createLinearGradientFillAndReturnFill(
    svgRoot: SVGSVGElement,
    angleDegrees: number,
    stops: [Color, number][]
): string {
    // Create a new linear gradient
    const gradientId = generateUniqueId();
    const gradient = createLinearGradient(gradientId, angleDegrees, stops);

    // Add it to the "defs" section of the SVG
    let defs = svgRoot.querySelector("defs");

    if (defs === null) {
        defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        svgRoot.appendChild(defs);
    }

    defs.appendChild(gradient);

    // Add the gradient to the path
    return `url(#${gradientId})`;
}

function createRadialGradientFillAndReturnFill(
    svgRoot: SVGSVGElement,
    centerX: number,
    centerY: number,
    stops: [Color, number][]
): string {
    // Create a new radial gradient
    const gradientId = generateUniqueId();
    const gradient = createRadialGradient(gradientId, centerX, centerY, stops);

    // Add it to the "defs" section of the SVG
    let defs = svgRoot.querySelector("defs");

    if (defs === null) {
        defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        svgRoot.appendChild(defs);
    }

    defs.appendChild(gradient);

    // Add the gradient to the path
    return `url(#${gradientId})`;
}

function createImageFillAndReturnFill(
    svgRoot: SVGSVGElement,
    imageUrl: string,
    fillMode: "fit" | "stretch" | "zoom" | "tile",
    tileSize: [number, number]
): string {
    // Tiling isn't supported. Map it to another mode for now.
    if (fillMode === "tile") {
        fillMode = "stretch";
    }

    // Prepare the aspect ratio
    let aspectRatio = {
        stretch: "none",
        fit: "xMidYMid meet", // FIXME
        zoom: "xMidYMid slice",
    }[fillMode];

    // Create a pattern
    const patternId = generateUniqueId();
    const pattern = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "pattern"
    );
    pattern.setAttribute("id", patternId);
    pattern.setAttribute("width", "100%");
    pattern.setAttribute("height", "100%");

    // Create an image
    const image = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "image"
    );
    image.setAttribute("href", imageUrl);
    image.setAttribute("width", "100%");
    image.setAttribute("height", "100%");
    image.setAttribute("preserveAspectRatio", aspectRatio);
    pattern.appendChild(image);

    // Add the pattern to the "defs" section of the SVG
    let defs = svgRoot.querySelector("defs");

    if (defs === null) {
        defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        svgRoot.appendChild(defs);
    }

    defs.appendChild(pattern);

    // Apply the pattern to the path
    return `url(#${patternId})`;
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
        "http://www.w3.org/2000/svg",
        "linearGradient"
    );
    gradient.setAttribute("id", gradientId);
    gradient.setAttribute("gradientTransform", `rotate(${angleDegrees})`);

    let ii = -1;
    for (const [color, offset] of stops) {
        ii += 1;

        const [r, g, b, a] = color;
        const stop = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "stop"
        );

        stop.setAttribute("offset", `${offset}`);
        stop.setAttribute(
            "style",
            `stop-color: rgba(${r * 255}, ${g * 255}, ${b * 255}, ${a})`
        );
        stop.setAttribute("id", `${gradientId}-stop-${ii}`);
        gradient.appendChild(stop);
    }

    return gradient;
}

function createRadialGradient(
    gradientId: string,
    centerX: number,
    centerY: number,
    stops: [Color, number][]
): SVGRadialGradientElement {
    const gradient = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "radialGradient"
    );
    gradient.setAttribute("id", gradientId);
    gradient.setAttribute("cx", `${centerX}`);
    gradient.setAttribute("cy", `${centerY}`);
    gradient.setAttribute("r", "0.5");
    gradient.setAttribute("fx", `${centerX}`);
    gradient.setAttribute("fy", `${centerY}`);

    let ii = -1;
    for (const [color, offset] of stops) {
        ii += 1;

        const [r, g, b, a] = color;
        const stop = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "stop"
        );

        stop.setAttribute("offset", `${offset}`);
        stop.setAttribute(
            "style",
            `stop-color: rgba(${r * 255}, ${g * 255}, ${b * 255}, ${a})`
        );
        stop.setAttribute("id", `${gradientId}-stop-${ii}`);
        gradient.appendChild(stop);
    }

    return gradient;
}

// Though the browser caches the icons for us, accessing the cached data
// requires an asynchronous function call, which can lead to noticeable delays.
// We'll make our own cache so that we can access the icons without ever
// entering async land.
const iconSvgCache = new Map<string, string>();
const RESOLVED_PROMISE = new Promise<void>((resolve) => resolve(undefined));

export async function loadIconSvg(iconName: string): Promise<string> {
    let svgSource = iconSvgCache.get(iconName);

    if (svgSource !== undefined) {
        return svgSource;
    }

    let response = await fetch(
        `${globalThis.RIO_BASE_URL}rio/icon/${iconName}`
    );
    svgSource = await response.text();

    iconSvgCache.set(iconName, svgSource);
    return svgSource;
}

export function applyIcon(
    target: HTMLElement,
    iconName: string,
    fill:
        | SolidFill
        | LinearGradientFill
        | RadialGradientFill
        | ImageFill
        | Color
        | ColorSet
        | "dim"
        | string = "var(--rio-local-text-color)" // A CSS color value
    // Note: We tried `currentColor` as the default value for the fill, but
    // that resulted in wrong colors somehow
): Promise<void> {
    function applySvg(svgSource: string) {
        // Apply the icon
        target.innerHTML = svgSource;

        // Apply the color
        let svgRoot = target.querySelector("svg") as SVGSVGElement;
        applyFillToSVG(svgRoot, fill);

        target.removeAttribute("data-rio-icon");
    }

    // Load the icon
    let svgSource = iconSvgCache.get(iconName);

    // Fast path: If it's already cached, apply the icon without ever entering
    // async land to avoid delays
    if (svgSource !== undefined) {
        applySvg(svgSource);
        return RESOLVED_PROMISE;
    }

    // Slow path: Load the icon from the server

    // Avoid races: When calling this function multiple times on the same
    // element it can sometimes assign the first icon AFTER the second one,
    // thus ending up with the wrong icon in the end.
    //
    // To avoid this, assign the icon that's supposed to be loaded into the
    // HTML element as a data attribute. Once the icon's source has been
    // fetched, only apply it if the data attribute still matches the icon
    // name.
    target.setAttribute("data-rio-icon", iconName);

    return loadIconSvg(iconName)
        .then((svgSource: string) => {
            // Check if the icon is still needed
            if (target.getAttribute("data-rio-icon") !== iconName) {
                return;
            }

            applySvg(svgSource);
        })
        .catch((reason) => {
            console.error(`Error loading icon ${iconName}: ${reason}`);
        });
}
