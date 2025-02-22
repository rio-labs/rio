import { pixelsPerRem } from "./app";
import { tryGetComponentByElement } from "./componentManagement";
import { ComponentBase } from "./components/componentBase";
import { ComponentLayout } from "./dataModels";
import { markEventAsHandled } from "./eventHandling";
import { callRemoteMethodDiscardResponse } from "./rpc";

let idCounter = 0;

export function createUniqueId(): number {
    idCounter++;
    return idCounter;
}

export function getPixelsPerRem(): number {
    let measure = document.createElement("div");
    measure.style.height = "10rem";
    document.body.appendChild(measure);
    let pixelsPerRem = measure.offsetHeight / 10;
    measure.remove();
    return pixelsPerRem;
}

let scrollBarSize: number | null = null;

export function getScrollBarSizeInPixels(): number {
    if (scrollBarSize === null) {
        scrollBarSize = _getScrollBarSizeInPixels();
    }

    return scrollBarSize;
}
function _getScrollBarSizeInPixels(): number {
    let outer = document.createElement("div");
    outer.style.position = "absolute";
    outer.style.top = "0px";
    outer.style.left = "0px";
    outer.style.visibility = "hidden";
    outer.style.width = "200px";
    outer.style.height = "150px";
    outer.style.overflow = "hidden";

    let inner = document.createElement("p");
    inner.style.width = "100%";
    inner.style.height = "200px";
    outer.appendChild(inner);

    document.body.appendChild(outer);
    let w1 = inner.offsetWidth;
    outer.style.overflow = "scroll";
    let w2 = inner.offsetWidth;
    if (w1 == w2) w2 = outer.clientWidth;

    document.body.removeChild(outer);

    return w1 - w2;
}

export class AsyncQueue<T> {
    private waitingForValue: ((value: T) => void)[] = [];
    private values: T[] = [];

    push(value: T): void {
        // If someone is waiting for a value, give it to them
        let notifyFirstWaiter = this.waitingForValue.shift();
        if (notifyFirstWaiter !== undefined) {
            notifyFirstWaiter(value);
            return;
        }

        // Otherwise, push it onto the stack
        this.values.push(value);
    }

    async get(): Promise<T> {
        // If a value exists in the queue, just return that
        let value = this.values.shift();
        if (value !== undefined) {
            return value;
        }

        // Otherwise, create a Promise that will be resolved when a new value is
        // added to the queue
        let waitForValue = new Promise((resolve: (value: T) => void) => {
            this.waitingForValue.push(resolve);
        });
        return await waitForValue;
    }
}

/// A ResizeObserver that doesn't invoke the callback function when it's
/// created, only on actual resizes.
export class OnlyResizeObserver {
    private elements: Element[];
    private callback: () => void;
    private ignoreNextCall: boolean = true;
    private resizeObserver: ResizeObserver;

    constructor(element: Element | Element[], callback: () => void) {
        if (!Array.isArray(element)) {
            element = [element];
        }

        this.elements = element;
        this.callback = callback;

        this.resizeObserver = new ResizeObserver(this._callback.bind(this));
        this.enable();
    }

    public disable(): void {
        this.resizeObserver.disconnect();
    }

    public enable(): void {
        for (let element of this.elements) {
            this.ignoreNextCall = true;
            this.resizeObserver.observe(element);
        }
    }

    public disconnect(): void {
        this.resizeObserver.disconnect();
    }

    private _callback(): void {
        if (this.ignoreNextCall) {
            this.ignoreNextCall = false;
            return;
        }

        this.callback();
    }
}

export function commitCss(element: HTMLElement): void {
    element.offsetHeight;
}

export function disableTransitions(element: HTMLElement) {
    element.style.transition = "none";
    element.offsetHeight;
}

export function enableTransitions(element: HTMLElement) {
    element.style.removeProperty("transition");
    element.offsetHeight;
}

export function withoutTransitions(
    element: HTMLElement,
    func: () => void
): void {
    disableTransitions(element);

    func();

    enableTransitions(element);
}

/// Asynchronously sleeps for the given number of seconds.
export async function sleep(durationInSeconds: number): Promise<void> {
    await new Promise((resolve, reject) =>
        setTimeout(resolve, durationInSeconds * 1000)
    );
}

export function reprElement(element: Element): string {
    let chunks = [element.tagName.toLowerCase()];

    for (let attr of element.attributes) {
        chunks.push(`${attr.name}=${JSON.stringify(attr.value)}`);
    }

    return `<${chunks.join(" ")}>`;
}

/// Returns an array containing all numbers from `start` (inclusive) to `end`
/// (exclusive).
export function range(start: number, end: number): number[] {
    let result: number[] = [];

    for (let ii = start; ii < end; ii++) {
        result.push(ii);
    }

    return result;
}

export function zip<T1, T2>(
    iterable1: Iterable<T1>,
    iterable2: Iterable<T2>
): Array<[T1, T2]> {
    const result: Array<[T1, T2]> = [];
    const iter1 = iterable1[Symbol.iterator]();
    const iter2 = iterable2[Symbol.iterator]();

    let next1 = iter1.next();
    let next2 = iter2.next();

    while (!next1.done && !next2.done) {
        result.push([next1.value, next2.value]);
        next1 = iter1.next();
        next2 = iter2.next();
    }

    return result;
}

/// Returns the first argument that isn't `undefined`. Throws an error if all
/// arguments are `undefined`.
export function firstDefined<T>(...args: (T | undefined)[]): T {
    for (let arg of args) {
        if (arg !== undefined) {
            return arg;
        }
    }

    throw new Error("All arguments were `undefined`");
}

/// Removes `oldElement` from the DOM and inserts `newElement` at its position
export function replaceElement(oldElement: Element, newElement: Node): void {
    oldElement.parentElement?.insertBefore(newElement, oldElement);
    oldElement.remove();
}

/// Wraps the given Element in a DIV
export function insertWrapperElement(wrappedElement: Element): HTMLElement {
    let wrapperElement = document.createElement("div");

    replaceElement(wrappedElement, wrapperElement);
    wrapperElement.appendChild(wrappedElement);

    return wrapperElement;
}

/// Adds a timeout to a promise. Throws TimeoutError if the time limit is
/// exceeded before the promise resolves.
export function timeout<T>(
    promise: Promise<T>,
    timeoutInSeconds: number
): Promise<T> {
    return Promise.race([promise, rejectAfter(timeoutInSeconds)]);
}

function rejectAfter(timeoutInSeconds: number): Promise<never> {
    return new Promise((resolve, reject) => {
        setTimeout(reject, timeoutInSeconds * 1000);
    });
}

export class TimeoutError extends Error {
    constructor(message: string) {
        super(message);
        this.name = this.constructor.name;
    }
}

export class ClipboardError extends Error {
    constructor(message: string) {
        super(message);
        this.name = this.constructor.name;
    }
}

export async function setClipboard(text: string): Promise<void> {
    if (navigator.clipboard) {
        try {
            await navigator.clipboard.writeText(text);
            return;
        } catch (error) {
            console.warn(`Failed to set clipboard content: ${error}`);
            throw new ClipboardError(
                `Failed to set clipboard content: ${error}`
            );
        }
    }

    // Fallback in case `navigator.clipboard` isn't available or didn't work
    if (document.execCommand) {
        const textArea = document.createElement("textarea");
        textArea.value = text;

        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        textArea.remove();
    }

    console.warn("Failed to set clipboard content: No clipboard API available");
    throw new ClipboardError(
        "Failed to set clipboard content: No clipboard API available"
    );
}

export async function getClipboard(): Promise<string> {
    if (navigator.clipboard) {
        try {
            return await navigator.clipboard.readText();
        } catch (error) {
            console.warn(`Failed to get clipboard content: ${error}`);
            throw new ClipboardError(
                `Failed to get clipboard content: ${error}`
            );
        }
    }

    throw new ClipboardError("Clipboard API is not available");
}

/// Checks if there's an #url-fragment, and if so, scrolls the corresponding
/// ScrollTarget into view
export function scrollToUrlFragment(
    behavior: "instant" | "smooth" = "smooth"
): void {
    let fragment = window.location.hash.substring(1);
    if (!fragment) {
        return;
    }

    let element = document.getElementById(fragment);
    if (element === null) {
        return;
    }

    element.scrollIntoView({ behavior: behavior });
}

/// Returns `true` if the given URL is local to this app and `false` otherwise.
function isLocalUrl(url: string): boolean {
    let parsedUrl = new URL(url);
    return parsedUrl.host === document.location.host;
}

/// Navigates to the given URL. If the URL is local to this app, does so without
/// reloading the page. Otherwise, does a full page reload.
export function navigateToUrl(url: string, openInNewTab: boolean): void {
    // TODO: If the websocket connection to the server is closed, handle it
    // locally even if it would usually be handled by the server

    // If only the url fragment is different, just scroll the relevant
    // element into view and we're done
    if (!openInNewTab) {
        let currentUrlWithoutHash = window.location.href.split("#")[0];
        let [urlWithoutHash, hash] = url.split("#");

        if (urlWithoutHash === currentUrlWithoutHash && hash) {
            window.location.hash = hash;
            scrollToUrlFragment();
            return;
        }
    }

    // First, decide whether we can do the navigation ourselves or if we have to
    // let the server handle it.
    //
    // Note: We don't want to needlessly close the session and create a new one,
    // so if the URL points to another page of the rio app, we'll also tell the
    // server about it instead of doing it ourselves.
    let sendToServer: boolean;

    // If it's not a HTTP(S) url, just let the browser/webview handle it
    if (!["http:", "https:"].includes(new URL(url).protocol.toLowerCase())) {
        sendToServer = false;
    }
    // If RUNNING_IN_WINDOW, the server has to do it for us:
    // - We can't open a new tab
    // - External urls must be opened in a new tab
    // - Local urls are sent to the server in order to keep this session alive
    else if (globalThis.RUNNING_IN_WINDOW) {
        sendToServer = true;
    }
    // If running in a browser and we're supposed to open a new tab, we can
    // do that.
    else if (openInNewTab) {
        sendToServer = false;
    }
    // If running in a browser and not opening a new tab, it depends on whether
    // it's an external url or not. Navigating to an external URL closes the
    // session anyways, so we can just navigate away. But for local urls it's
    // more efficient to let the server handle it.
    else {
        sendToServer = isLocalUrl(url);
    }

    if (sendToServer) {
        // The server knows exactly what to do with the URL, so it doesn't even
        // accept a `openInNewTab` argument
        callRemoteMethodDiscardResponse("openUrl", { url: url });
    } else if (openInNewTab) {
        let link = document.createElement("a");
        link.href = url;
        link.target = "_blank";
        link.click();
    } else {
        window.location.href = url;
    }
}

/// Augments the given link element with Rio specific URL handling logic. This
/// is a convenience function that essentially runs `navigateToUrl` when the
/// link is clicked.
export function hijackLinkElement(linkElement: HTMLAnchorElement) {
    linkElement.addEventListener(
        "click",
        (event: MouseEvent) => {
            let openInNewTab: boolean;

            if (event.button === 0) {
                openInNewTab =
                    linkElement.target === "_blank" ||
                    event.ctrlKey ||
                    event.metaKey;
            } else if (event.button === 1) {
                openInNewTab = true;
            } else {
                return;
            }

            markEventAsHandled(event);

            navigateToUrl(linkElement.href, openInNewTab);
        },
        true
    );
}

/// Returns the component at the position of the given MouseEvent. Excludes
/// internal components. (Basically, if it wouldn't be visible in the Component
/// Tree in the dev sidebar, it doesn't count.)
export function findComponentUnderMouse(
    event: MouseEvent
): ComponentBase | null {
    // The coordinates for `elementFromPoint` are relative to the viewport. This
    // matches `event.clientX` and `event.clientY`.
    let element = document.elementFromPoint(event.clientX, event.clientY);

    // It could be an internal element. Go up the tree until we find a Component
    while (element !== null) {
        let component = tryGetComponentByElement(element);

        if (component !== null && !component.state._rio_internal_) {
            return component;
        }

        element = element.parentElement;
    }

    return null;
}

/// Determines the preferred format string for dates in the given locale. The
/// string is suitable for use with Python's `strftime` function.
export function getPreferredPythonDateFormatString(locale: string): string {
    /// Format an already known date
    let formattedDate = new Date(3333, 2, 1).toLocaleDateString(locale, {
        year: "numeric",
        month: "numeric",
        day: "numeric",
    });

    /// Parse the format string
    formattedDate = formattedDate.replace("3333", "%Y");
    formattedDate = formattedDate.replace("33", "%y");

    formattedDate = formattedDate.replace("03", "%m");
    formattedDate = formattedDate.replace("3", "%m"); // %-m is not supported on Windows

    formattedDate = formattedDate.replace("01", "%d");
    formattedDate = formattedDate.replace("1", "%d"); // %-d is not supported on Windows

    return formattedDate;
}

/// Gathers layout information for the given components.
export function getComponentLayout(component: ComponentBase): ComponentLayout {
    let result = {} as ComponentLayout;
    let outerElement = component.outerElement;
    let innerElement = component.element;

    // Id of the parent component
    let parentComponent = component.parent;

    if (parentComponent === null) {
        result.parentId = null;
    } else {
        result.parentId = parentComponent.id;
    }

    // Position in the viewport
    let outerRect = outerElement.getBoundingClientRect();
    result.leftInViewportOuter = outerRect.left / pixelsPerRem;
    result.topInViewportOuter = outerRect.top / pixelsPerRem;

    let innerRect = innerElement.getBoundingClientRect();
    result.leftInViewportInner = innerRect.left / pixelsPerRem;
    result.topInViewportInner = innerRect.top / pixelsPerRem;

    // Allocated size
    result.allocatedOuterWidth =
        getAllocatedWidthInPx(outerElement) / pixelsPerRem;
    result.allocatedOuterHeight =
        getAllocatedHeightInPx(outerElement) / pixelsPerRem;

    result.allocatedInnerWidth =
        getAllocatedWidthInPx(innerElement) / pixelsPerRem;
    result.allocatedInnerHeight =
        getAllocatedHeightInPx(innerElement) / pixelsPerRem;

    let naturalSizeInPixels = getNaturalSizeInPixels(innerElement);
    result.naturalWidth = naturalSizeInPixels[0] / pixelsPerRem;
    result.naturalHeight = naturalSizeInPixels[1] / pixelsPerRem;

    // The requested size is the maximum of the natural size and the explicitly
    // provided size
    result.requestedInnerWidth = Math.max(
        result.naturalWidth,
        component.state._min_size_[0]
    );

    result.requestedInnerHeight = Math.max(
        result.naturalHeight,
        component.state._min_size_[1]
    );

    // Apply margins to arrive at the requested outer size
    result.requestedOuterWidth =
        result.requestedInnerWidth +
        component.state._margin_[0] +
        component.state._margin_[2];
    result.requestedOuterHeight =
        result.requestedInnerHeight +
        component.state._margin_[1] +
        component.state._margin_[3];

    // Done
    return result;
}
globalThis.getComponentLayout = getComponentLayout;

export function getNaturalSizeInPixels(element: HTMLElement): [number, number] {
    // In order to determine the natural size, the component needs to be removed
    // from the DOM. This way its size isn't influenced by any surrounding
    // elements.
    //
    // Note: This can mess up the parent elements' scroll positions, since their
    // content is suddenly smaller than before!
    let parentElement = element.parentElement!;
    let previousSibling = element.previousSibling;

    let originalDisplay = element.style.display;
    let originalPosition = element.style.position;
    let originalMinWidth = element.style.minWidth;
    let originalMinHeight = element.style.minHeight;
    let originalWidth = element.style.width;
    let originalHeight = element.style.height;

    let allocatedWidth = element.scrollWidth;

    document.body.appendChild(element);

    // Determine the natural size
    if (originalDisplay === "none") {
        element.style.display = "block";
    }

    element.style.position = "absolute";
    element.style.removeProperty("min-width");
    element.style.removeProperty("min-height");
    element.style.width = "min-content";
    element.style.height = "min-content";
    let naturalWidth = element.offsetWidth;

    element.style.width = `${allocatedWidth}px`;
    let naturalHeight = element.offsetHeight;

    // Return the component to its original state
    parentElement.insertBefore(element, previousSibling);

    element.style.display = originalDisplay;
    element.style.position = originalPosition;
    element.style.minWidth = originalMinWidth;
    element.style.minHeight = originalMinHeight;
    element.style.width = originalWidth;
    element.style.height = originalHeight;

    return [naturalWidth, naturalHeight];
}

globalThis.getNaturalSizeInPixels = getNaturalSizeInPixels;

// Unlike `getBoundingClientRect`, which returns the size of the element *in the
// viewport* and is thus affected by things like `filter: scale(0)`, these
// functions return the width and height of an element that's relevant for our
// layouting system.
export function getAllocatedWidthInPx(element: HTMLElement): number {
    return element.offsetWidth;
}
export function getAllocatedHeightInPx(element: HTMLElement): number {
    return element.offsetHeight;
}

export function camelToKebab(text: string): string {
    return text.replace(/([a-z])([A-Z])/g, "$1-$2").toLowerCase();
}
