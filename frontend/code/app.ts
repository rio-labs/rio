import { getComponentByElement } from './componentManagement';
import { Debouncer } from './debouncer';
import { updateLayout } from './layouting';
import {
    callRemoteMethodDiscardResponse,
    incomingMessageQueue,
    initWebsocket,
} from './rpc';
import { scrollToUrlFragment } from './utils';

// If a the devtools are present it is exposed here so the codebase can notify it as
// needed. This is an instance of `DevToolsConnectorComponent`.
globalThis.RIO_DEV_TOOLS = null;

// Set to indicate that we're intentionally leaving the page. This can be used
// to suppress the connection lost popup, reconnects, or similar
export let goingAway: boolean = false;

function getScrollBarWidthInPixels(): number {
    let outer = document.createElement('div');
    outer.style.position = 'absolute';
    outer.style.top = '0px';
    outer.style.left = '0px';
    outer.style.visibility = 'hidden';
    outer.style.width = '200px';
    outer.style.height = '150px';
    outer.style.overflow = 'hidden';

    let inner = document.createElement('p');
    inner.style.width = '100%';
    inner.style.height = '200px';
    outer.appendChild(inner);

    document.body.appendChild(outer);
    let w1 = inner.offsetWidth;
    outer.style.overflow = 'scroll';
    let w2 = inner.offsetWidth;
    if (w1 == w2) w2 = outer.clientWidth;

    document.body.removeChild(outer);

    return w1 - w2;
}

const SCROLL_BAR_SIZE_IN_PIXELS = getScrollBarWidthInPixels();

export let pixelsPerRem = 16;
export let scrollBarSize = SCROLL_BAR_SIZE_IN_PIXELS / pixelsPerRem;

let notifyBackendOfWindowSizeChange = new Debouncer({
    callback: (newWidthPx: number, newHeightPx: number) => {
        try {
            callRemoteMethodDiscardResponse('onWindowSizeChange', {
                newWidth: newWidthPx / pixelsPerRem,
                newHeight: newHeightPx / pixelsPerRem,
            });
        } catch (e) {
            console.warn(`Couldn't notify backend of window resize: ${e}`);
        }
    },
});

async function main(): Promise<void> {
    // Display a warning if running in debug mode
    if (globalThis.RIO_DEBUG_MODE) {
        console.warn(
            'Rio is running in DEBUG mode.\nDebug mode includes helpful tools' +
                ' for development, but is slower and disables some safety checks.' +
                ' Never use it in production!'
        );
    }

    // Wait until the CSS has loaded
    await globalThis.cssLoaded;

    // Determine the browser's font size
    var measure = document.createElement('div');
    measure.style.height = '10rem';
    document.body.appendChild(measure);
    pixelsPerRem = measure.offsetHeight / 10;
    document.body.removeChild(measure);

    scrollBarSize = SCROLL_BAR_SIZE_IN_PIXELS / pixelsPerRem;

    // TEMP, for debugging
    globalThis.pixelsPerRem = pixelsPerRem;
    globalThis.scrollBarSize = scrollBarSize;

    window.addEventListener('beforeunload', () => {
        goingAway = true;
    });

    // Note: I'm not sure if this event is ever triggered. The smooth scrolling
    // is actually implemented in `popstate` and in the CSS.
    window.addEventListener('hashchange', (event) => {
        console.log(
            `hashchange event triggered; new URL is ${window.location.href}`
        );

        scrollToUrlFragment();
    });

    // Listen for URL changes, so the session can switch page
    window.addEventListener('popstate', (event: PopStateEvent) => {
        console.debug(
            `popstate event triggered; new URL is ${window.location.href}`
        );

        // This event is also triggered if the user manually types in a URL
        // fragment. So we need to check which part of the url has changed and
        // act accordingly. If it was only the url fragment, we'll simply scroll
        // the relevant ScrollTarget into view.
        //
        // NOTE: If we send a `onUrlChange` message to the server, it'll cause a
        // rebuild of all PageViews and scroll to the top of the page. This is
        // why we *EITHER* send a `onUrlChange` message *OR* scroll to the
        // ScrollTarget, but not both.

        // FIXME: Find a way to tell whether only the url fragment changed
        console.debug(`URL changed to ${window.location.href}`);
        callRemoteMethodDiscardResponse('onUrlChange', {
            newUrl: window.location.href.toString(),
        });
    });

    // Listen for resize events
    window.addEventListener('resize', (event) => {
        // Notify the backend
        notifyBackendOfWindowSizeChange.call(
            window.innerWidth,
            window.innerHeight
        );

        // Re-layout, but only if a root component already exists
        let rootElement = document.body.querySelector(
            '.rio-fundamental-root-component'
        );

        if (rootElement !== null) {
            let rootInstance = getComponentByElement(
                rootElement as HTMLElement
            );
            rootInstance.makeLayoutDirty();
            updateLayout();
        }
    });

    // Process initial messages
    for (let message of globalThis.initialMessages) {
        incomingMessageQueue.push(message);
    }
    delete globalThis.initialMessages;

    // Connect to the websocket
    initWebsocket();
}

main();
