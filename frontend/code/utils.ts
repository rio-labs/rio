import { pixelsPerRem } from './app';
import { ComponentBase } from './components/componentBase';
import { ComponentLayout } from './dataModels';
import { markEventAsHandled } from './eventHandling';
import { callRemoteMethodDiscardResponse } from './rpc';

export function getPixelsPerRem(): number {
    let measure = document.createElement('div');
    measure.style.height = '10rem';
    document.body.appendChild(measure);
    let pixelsPerRem = measure.offsetHeight / 10;
    measure.remove();
    return pixelsPerRem;
}

// Returns the size of the window, minus the space occupied by the dev tools, in
// rem
export function getUsableWindowSize(): [number, number] {
    let element = globalThis.RIO_DEBUG_MODE
        ? document.querySelector('.rio-user-root-container-outer')!
        : document.documentElement;

    let rect = element.getBoundingClientRect();
    return [rect.width / pixelsPerRem, rect.height / pixelsPerRem];
}

/// Scrolls an element into view and waits until the scrolling is complete.
/// Useful if you need to run code after scrolling.
export async function scrollToElement(element: Element): Promise<void> {
    // Note: If you're thinking of using the `scroll` or `scrollend` event,
    // forget it. I tried, it doesn't work. I think it's because there are
    // multiple scrolling elements involved, and those events only trigger when
    // the <html> element itself scrolls.

    element.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'nearest',
    });

    // Note: This doesn't only detect scrolling, it also detects movement of the
    // element. But I can't think of a better solution.

    // Note 2: If it seems like this function is weirdly delayed, it's probably
    // not the function's fault, but caused by smooth scrolling. I tested in
    // Firefox, and it took 200ms to scroll the last 5 pixels.
    let rect = element.getBoundingClientRect();
    while (true) {
        await sleep(0.05);

        let newRect = element.getBoundingClientRect();

        if (newRect.left === rect.left && newRect.top === rect.top) {
            return;
        }

        rect = newRect;
    }
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

export function commitCss(element: HTMLElement): void {
    element.offsetHeight;
}

export function disableTransitions(element: HTMLElement) {
    element.style.transition = 'none';
    element.offsetHeight;
}

export function enableTransitions(element: HTMLElement) {
    element.style.removeProperty('transition');
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

    return `<${chunks.join(' ')}>`;
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

/// Returns the first argument that isn't `undefined`. Returns `undefined` if
/// none of the arguments are defined.
export function firstDefined(...args: any[]): any {
    for (let arg of args) {
        if (arg !== undefined) {
            return arg;
        }
    }

    return undefined;
}

/// Removes `oldElement` from the DOM and inserts `newElement` at its position
export function replaceElement(oldElement: Element, newElement: Node): void {
    oldElement.parentElement?.insertBefore(newElement, oldElement);
    oldElement.remove();
}

/// Wraps the given Element in a DIV
export function insertWrapperElement(wrappedElement: Element): HTMLElement {
    let wrapperElement = document.createElement('div');

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
        const textArea = document.createElement('textarea');
        textArea.value = text;

        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
    }

    console.warn('Failed to set clipboard content: No clipboard API available');
    throw new ClipboardError(
        'Failed to set clipboard content: No clipboard API available'
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

    throw new ClipboardError('Clipboard API is not available');
}

/// Checks if there's an #url-fragment, and if so, scrolls the corresponding
/// ScrollTarget into view
export function scrollToUrlFragment(
    behavior: 'instant' | 'smooth' = 'smooth'
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
        let currentUrlWithoutHash = window.location.href.split('#')[0];
        let [urlWithoutHash, hash] = url.split('#');

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
    if (!['http:', 'https:'].includes(new URL(url).protocol.toLowerCase())) {
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
        callRemoteMethodDiscardResponse('openUrl', { url: url });
    } else if (openInNewTab) {
        let link = document.createElement('a');
        link.href = url;
        link.target = '_blank';
        link.click();
    } else {
        window.location.href = url;
    }
}

export function hijackLinkElement(linkElement: HTMLAnchorElement) {
    linkElement.addEventListener(
        'click',
        (event) => {
            let openInNewTab: boolean;

            if (event.button === 0) {
                openInNewTab = linkElement.target === '_blank';
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

/// Determines the preferred format string for dates in the given locale. The
/// string is suitable for use with Python's `strftime` function.
export function getPreferredPythonDateFormatString(locale: string): string {
    /// Format an already known date
    let formattedDate = new Date(3333, 2, 1).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
    });

    /// Parse the format string
    formattedDate = formattedDate.replace('3333', '%Y');
    formattedDate = formattedDate.replace('33', '%y');

    formattedDate = formattedDate.replace('03', '%m');
    formattedDate = formattedDate.replace('3', '%m'); // %-m is not supported on Windows

    formattedDate = formattedDate.replace('01', '%d');
    formattedDate = formattedDate.replace('1', '%d'); // %-d is not supported on Windows

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

    let innerRect = component.element.getBoundingClientRect();
    result.leftInViewportInner = innerRect.left / pixelsPerRem;
    result.topInViewportInner = innerRect.top / pixelsPerRem;

    // Allocated size
    result.allocatedOuterWidth = outerRect.width / pixelsPerRem;
    result.allocatedOuterHeight = outerRect.height / pixelsPerRem;

    result.allocatedInnerWidth = innerRect.width / pixelsPerRem;
    result.allocatedInnerHeight = innerRect.height / pixelsPerRem;

    // In order to determine the some layout properties the component needs to
    // be removed from the DOM. This way its size isn't influenced by any
    // surrounding elements.
    {
        let parentElement = innerElement.parentElement as HTMLElement;
        let previousSibling = innerElement.previousSibling;

        let originalPosition = innerElement.style.position;
        let originalWidth = innerElement.style.width;
        let originalHeight = innerElement.style.height;

        document.body.appendChild(innerElement);

        // Determine the natural size
        innerElement.style.position = 'absolute';
        innerElement.style.width = 'min-content';
        innerElement.style.height = 'min-content';
        result.naturalWidth = innerElement.offsetWidth / pixelsPerRem;

        innerElement.style.width = `${result.allocatedInnerWidth}rem`;
        result.naturalHeight = innerElement.offsetHeight / pixelsPerRem;

        // Return the component to its original state
        parentElement.insertBefore(innerElement, previousSibling);

        innerElement.style.position = originalPosition;
        innerElement.style.width = originalWidth;
        innerElement.style.height = originalHeight;
    }

    // The requested size is the maximum of the natural size and the explicitly
    // provided size
    result.requestedInnerWidth = Math.max(
        result.naturalWidth,
        component.state._size_[0]
    );

    result.requestedInnerHeight = Math.max(
        result.naturalHeight,
        component.state._size_[1]
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
