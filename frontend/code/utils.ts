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
export function isLocalUrl(url: string): boolean {
    let parsedUrl = new URL(url);
    return parsedUrl.hostname === document.location.hostname;
}

/// Navigates to the given URL. If the URL is local to this app, does so without
/// reloading the page. Otherwise, does a full page reload.
export function navigateToUrl(url: string): void {
    // If the URL is local simply inform the server to switch to the new page
    if (isLocalUrl(url)) {
        console.debug('Navigating to local URL:', url);

        callRemoteMethodDiscardResponse('openUrl', {
            url: url,
        });
        return;
    }

    // Otherwise, do a full page reload
    console.debug('Navigating to external URL:', url);
    window.location.href = url;
}
