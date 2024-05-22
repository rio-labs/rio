import { componentsByElement } from './componentManagement';
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

/// Returns the first argument that isn't `undefined`.
export function firstDefined(...args: any[]): any {
    for (let arg of args) {
        if (arg !== undefined) {
            return arg;
        }
    }

    return undefined;
}

/// Copies the given text to the clipboard
export function copyToClipboard(text: string): void {
    const textArea = document.createElement('textarea');
    textArea.value = text;

    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
}

/// Checks if there's an #url-fragment, and if so, scrolls the corresponding
/// ScrollTarget into view
export function scrollToUrlFragment(): void {
    let fragment = window.location.hash.substring(1);
    if (!fragment) {
        return;
    }

    let element = document.getElementById(fragment);
    if (element === null) {
        return;
    }

    element.scrollIntoView();
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

    // First, decide whether we can do the navigation ourselves or if we have to
    // let the server handle it.
    //
    // Note: We don't want to needlessly close the session and create a new one,
    // so if the URL points to another page of the rio app, we'll also tell the
    // server about it instead of doing it ourselves.
    let sendToServer: boolean;

    // If RUNNING_IN_WINDOW, the server has to do it for us:
    // - We can't open a new tab
    // - External urls must be opened in a new tab
    // - Local urls are sent to the server in order to keep this session alive
    if (globalThis.RUNNING_IN_WINDOW) {
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
        callRemoteMethodDiscardResponse('openUrl', {
            url: url,
            openInNewTab: openInNewTab,
        });
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

            console.log(new URL(linkElement.href), openInNewTab);
            navigateToUrl(linkElement.href, openInNewTab);
        },
        true
    );
}
