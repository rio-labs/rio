import { pixelsPerRem } from './app';
import { componentsById } from './componentManagement';
import { ComponentBase } from './components/componentBase';
import { callRemoteMethodDiscardResponse } from './rpc';

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
        document.body.removeChild(textArea);
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

            event.stopPropagation();
            event.preventDefault();

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

/// Given a component, finds the injected alignment component that corresponds
/// to it. Returns `null` if this component doesn't have an alignment component.
function findAlignmentForComponent(
    component: ComponentBase
): ComponentBase | null {
    // Get the parent component
    let result = component.parent;

    // If this is an injected margin, get the parent yet again
    if (
        result !== null &&
        result.state._type_ === 'Margin-builtin' &&
        result.isInjectedLayoutComponent()
    ) {
        result = result.parent;
    }

    // If this is an injected alignment, we've hit gold
    if (
        result !== null &&
        result.state._type_ === 'Align-builtin' &&
        result.isInjectedLayoutComponent()
    ) {
        return result;
    }

    return null;
}

/// Gathers layout information for the given components.
export async function getComponentLayouts(
    componentIds: number[]
): Promise<(object | null)[]> {
    let result: (object | null)[] = [];

    for (let componentId of componentIds) {
        {
            // Find the component
            let component: ComponentBase = componentsById[componentId];

            if (component === undefined) {
                result.push(null);
                continue;
            }

            // And its parent
            let parentComponent = component.getParentExcludingInjected()!;

            if (parentComponent === null) {
                result.push(null);
                continue;
            }

            // Position in the viewport
            let rect = component.element.getBoundingClientRect();
            let left_in_viewport = rect.left / pixelsPerRem;
            let top_in_viewport = rect.top / pixelsPerRem;

            // Position in the parent
            let parentRect = parentComponent.element.getBoundingClientRect();
            let left_in_parent = (rect.left - parentRect.left) / pixelsPerRem;
            let top_in_parent = (rect.top - parentRect.top) / pixelsPerRem;

            // Find the alignment component, if any
            let injectedAlignmentComponent =
                findAlignmentForComponent(component);

            let allocated_width_before_alignment,
                allocated_height_before_alignment;

            if (injectedAlignmentComponent === null) {
                allocated_width_before_alignment = rect.width / pixelsPerRem;
                allocated_height_before_alignment = rect.height / pixelsPerRem;
            } else {
                allocated_width_before_alignment =
                    injectedAlignmentComponent.allocatedWidth;
                allocated_height_before_alignment =
                    injectedAlignmentComponent.allocatedHeight;
            }

            // Store the subresult
            result.push({
                left_in_viewport: left_in_viewport,
                top_in_viewport: top_in_viewport,
                left_in_parent: left_in_parent,
                top_in_parent: top_in_parent,
                natural_width: component.naturalWidth,
                natural_height: component.naturalHeight,
                allocated_width: rect.width / pixelsPerRem,
                allocated_height: rect.height / pixelsPerRem,
                allocated_width_before_alignment:
                    allocated_width_before_alignment,
                allocated_height_before_alignment:
                    allocated_height_before_alignment,
                parent_id: parentComponent.id,
                parent_natural_width: parentComponent.naturalWidth,
                parent_natural_height: parentComponent.naturalHeight,
                parent_allocated_width: parentComponent.allocatedWidth,
                parent_allocated_height: parentComponent.allocatedHeight,
            });
        }
    }

    return result;
}
